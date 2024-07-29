from starlette.config import Config
from fastapi import APIRouter, Request
import os
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2AuthorizationCodeBearer
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from typing import Dict, List
import jwt
import uuid
from datetime import datetime, timedelta 

from app.model.credential import VerifiableCredential, CredentialSubject

"""
This file contains the OIDC endpoints for the OID4VCI specification.
"""

router = APIRouter()


# In-memory credential storage (replace with a database in production)
credentials: Dict[str, VerifiableCredential] = {}
pre_authorized_codes: Dict[str, Dict] = {}

ISSUER_DID = "did:example:123456789abcdefghi"

@router.get("/.well-known/openid-credential-issuer")
async def credential_issuer_metadata(request: Request):
    """
    This endpoint is created according to draft 13 of the oid4vci specification,
    which can be found here: 
    https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-credential-issuer-metadata-p.
    """
    host = request.headers.get("host", "localhost")
    scheme = request.headers.get("x-forwarded-proto", "http")
    base_url = f"{scheme}://{host}"
    return {
        "credential_issuer": ISSUER_DID,
        "credential_endpoint": f"{base_url}/credential",
        "authorization_endpoint": f"{base_url}/auth",
        "token_endpoint": f"{base_url}/token",
        "jwks_uri": f"{base_url}/jwks",
        "credential_types_supported": ["VerifiableCredential", "ProfileCredential"],
        "credentials_supported": {
            "ProfileCredential": {
                "types": ["VerifiableCredential", "ProfileCredential"],
                "format": "jwt_vc",
            }
        },
    }

@router.post("/credential-offer")
async def credential_offer():
    pre_auth_code = str(uuid.uuid4())
    pre_authorized_codes[pre_auth_code] = {
        "exp": datetime.utcnow() + timedelta(minutes=5),
        "credential_type": "ProfileCredential"
    }
    return {
        "credential_issuer": ISSUER_DID,
        "credentials": ["ProfileCredential"],
        "grants": {
            "urn:ietf:params:oauth:grant-type:pre-authorized_code": {
                "pre-authorized_code": pre_auth_code,
                "tx_code": {
                    "input_mode": "numeric",
                    "length": 6,
                    "description": "Please enter the 6-digit code displayed on your device"
                }
            }
        }
    }

"""
Token endpoint. The wallet till send a post request to this endpoint, and that will contain a tx code and a pre 
authorized code. The pre authorized code we will check up against the pre authorized code registered with us. 
If it matches, it will later (when we have created support for it) return the access token of the logged in user.
"""
@router.post("/token")
def token(request:Request) :
    #Fills data with the parameters from the xxx urlencoded content which posts to
    #our endpoint
    data = request.form

    #Checks if it is supposed to follow pre-autorized code run.
    grant_type = data.get('grant_type')
    if grant_type == "urn:ietf:params:oauth:grant-type:pre-authorized_code":

        #Gets and sets the parts of the url encoded content.
        pre_authorized_code = data.get('pre-authorized_code')
        # todo
        tx_code = data.get('tx_code')

        #If the pre autorized code is not same as the one set earlier in credential offer, exception.
        if pre_authorized_code not in pre_authorized_codes:
            raise HTTPException(status_code=400, detail="Invalid pre-authorized code")
        #Else, it now will send a fake access token, with the required information.
        response = {
            "accessToken": "eyRANDOMACCESSTOKEN",
            "token_type": "bearer",
            "expires_in": 86400,
            "c_nonce": "lolololol",
            "c_nonce_expires_in": 86400,
            "authorization_details": [
                {
                    "type": "openid_credential",
                    "credential_configuration_id": "UniversityDegreeCredential",
                    "credential_identifiers": [
                        "CivilEngineeringDegree-2023",
                        "ElectricalEngineeringDegree-2023"
                    ]
                }
            ]
        }

        #Headers neeed to be this, according to draft 13 oid4vci.
        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-store"
        }

        #Sets headers to the response we will send.
        response.headers = headers

        #Sends the response back so that the wallet gets the id token in return.
        return {request}

    #If the grant type is not pre-autorized flow:
    else : raise HTTPException(status_code=418, detail="Service only supports pre autorized flow.")



@router.post("/credential")
async def issue_credential(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    pre_auth_code = payload["sub"]
    if pre_auth_code not in pre_authorized_codes:
        raise HTTPException(status_code=400, detail="Invalid pre-authorized code")
    
    credential_type = pre_authorized_codes[pre_auth_code]["credential_type"]
    
    # In a real scenario, you would fetch user data from a secure source
    user_data = {"id": str(uuid.uuid4()), "email": "user@example.com", "name": "John Doe"}
    
    credential = VerifiableCredential(
        id=f"urn:uuid:{uuid.uuid4()}",
        type=["VerifiableCredential", credential_type],
        issuer=ISSUER_DID,
        issuanceDate=datetime.utcnow().isoformat() + "Z",
        credentialSubject=CredentialSubject(**user_data)
    )
    
    credentials[credential.id] = credential
    
    # In a real scenario, you would sign the credential here
    
    return JSONResponse(content=credential.dict())
