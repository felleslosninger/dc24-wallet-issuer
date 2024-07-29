from starlette.config import Config
from fastapi import APIRouter, Request
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from fastapi.templating import Jinja2Templates
import json

import jwt
import uuid
import os
from typing import Dict
from datetime import datetime, timedelta 

from app.model.credential import VerifiableCredential, CredentialSubject
from app.service.misc import get_base_url
from app.service.qr_code_service import generate_qr_code
from app.service.credential_service import create_pre_auth_credential
from app.service.misc import templates

"""
This file contains the OIDC endpoints for the OID4VCI specification.
"""

router = APIRouter()

# In-memory credential storage (replace with a database in production)
credentials: Dict[str, VerifiableCredential] = {}
pre_authorized_codes: Dict[str, Dict] = {}

@router.get("/.well-known/openid-credential-issuer")
async def credential_issuer_metadata(request: Request):
    """
    This endpoint is created according to draft 13 of the oid4vci specification
    section 11, which can be found here: 
    https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-credential-issuer-metadata-p.
    """
    base_url = get_base_url(request)
    return {
        "credential_issuer": base_url,
        "credential_endpoint": f"{base_url}/credential",
        #"credential_types_supported": ["VerifiableCredential", "ProfileCredential"],
        "credential_configurations_supported": {
            "eu.europa.ec.eudi.pid_jwt_vc_json": {
                "format": "jwt_vc_json", # TODO: finne ut hvilket format som er lettest
                "scope": "openid profile difitest:guardian", # Usikker på m denne trengs her, men 
                "types": ["VerifiableCredential", "ProfileCredential"],
            }
        },
    }

@router.get("/credential-offer")
async def credential_offer(request: Request):
    pre_auth_code = str(uuid.uuid4())
    pre_authorized_codes[pre_auth_code] = {
        "exp": datetime.now() + timedelta(minutes=5),
        "credential_type": "eu.europa.ec.eudi.pid_jwt_vc_json"
    }
    return {
        "credential_issuer": get_base_url(request),
        "credentials": ["eu.europa.ec.eudi.pid_jwt_vc_json"],
        "grants": {
            "urn:ietf:params:oauth:grant-type:pre-authorized_code": {
                "pre-authorized_code": pre_auth_code,
                #"tx_code": {
                #    "input_mode": "numeric",
                #     "length": 6,
                #     "description": "Please enter the 6-digit code displayed on your device"
                # }
            }
        }
    }
    
@router.get("/credential/qr-code")
async def credential_offer_qr(request: Request):
    base_redirect_uri = "openid-credential-offer://"
    qr_code = generate_qr_code(base_redirect_uri + json.dumps(create_pre_auth_credential(request)))
    return templates.TemplateResponse("qr_code.html", {"qr_code": qr_code})
    

@router.post("/token")
async def token(request: Request):
    form_data = await request.form()
    grant_type = form_data.get("grant_type")
    
    if grant_type == "urn:ietf:params:oauth:grant-type:pre-authorized_code":
        pre_auth_code = form_data.get("pre-authorized_code")
        tx_code = form_data.get("tx_code")
        
        if pre_auth_code not in pre_authorized_codes:
            raise HTTPException(status_code=400, detail="Invalid pre-authorized code")
        
        if datetime.utcnow() > pre_authorized_codes[pre_auth_code]["exp"]:
            raise HTTPException(status_code=400, detail="Pre-authorized code expired")
        
        # In a real scenario, verify tx_code here
        
        access_token = jwt.encode({"sub": pre_auth_code, "exp": datetime.utcnow() + timedelta(minutes=5)}, os.getenv("JWT_SECRET_KEY"), algorithm="HS256")
        return {"access_token": access_token, "token_type": "Bearer"}
    
    raise HTTPException(status_code=400, detail="Unsupported grant type")

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
