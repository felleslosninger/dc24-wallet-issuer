from starlette.config import Config
from fastapi import Request, HTTPException, APIRouter, Header
from fastapi.responses import JSONResponse
from starlette.config import Config
from urllib.parse import parse_qs
from pymdoccbor.mdoc.issuer import MdocCborIssuer
from cryptography.hazmat.primitives import serialization

import uuid
import base64
from typing import Dict, Optional
from datetime import datetime, timedelta

from app.routes.oauth import getLoggedInUsersToken
from app.service.misc import get_base_url
from app.service.qr_code_service import generate_qr_code
from app.service.misc import templates

"""
This file contains the OIDC endpoints for the OID4VCI specification.
"""

router = APIRouter()

config = Config('.env')

# In-memory credential storage (replace with a database in production)
pre_authorized_codes: Dict[str, Dict] = {}

def create_pre_auth_credential_offer(request: Request, pre_auth_code: str):
    return {
        "credential_issuer": get_base_url(request),
        "credential_configuration_ids": [
            "eu.europa.ec.eudi.loyalty_mdoc"
        ],
        "grants": {
            "urn:ietf:params:oauth:grant-type:pre-authorized_code": {
                "pre-authorized_code": pre_auth_code,
                "tx_code": {
                    "length": 6,
                    "input_mode": "numeric",
                    "description": "Please provide the one-time code that is 123456"
                }
            }
        }
    }
    
@router.get("/.well-known/openid-configuration")
async def openid_configuration(request: Request):
    base_url = get_base_url(request)
    return {
  "request_parameter_supported": False,
  "pushed_authorization_request_endpoint": base_url + "/par",
  "authorization_response_iss_parameter_supported": True,
  "introspection_endpoint": base_url + "/token/introspect",
  "claims_parameter_supported": False,
  "scopes_supported": [
    "openid",
    "profile"
  ],
  "issuer": base_url + "",
  "acr_values_supported": [
    "idporten-loa-low",
    "idporten-loa-substantial",
    "idporten-loa-high",
    "eidas-loa-low",
    "eidas-loa-substantial",
    "eidas-loa-high"
  ],
  "authorization_endpoint": "https://login.test.idporten.no/authorize",
  "display_values_supported": [
    "page"
  ],
  "token_endpoint_auth_methods_supported": [
    "client_secret_basic",
    "client_secret_post",
    "none",
    "private_key_jwt"
  ],
  "response_modes_supported": [
    "query",
    "form_post",
    "query.jwt",
    "form_post.jwt"
  ],
  "token_endpoint": base_url + "/token",
  "response_types_supported": [
    "code"
  ],
  "request_uri_parameter_supported": False,
  "grant_types_supported": [
    "authorization_code",
    "refresh_token"
  ],
  "ui_locales_supported": [
    "en",
    "nb",
    "nn",
    "se"
  ],
  "end_session_endpoint": "https://login.test.idporten.no/logout",
  "revocation_endpoint": base_url + "/token/revoke",
  "prompt_values_supported": [
    "consent",
    "login",
    "none"
  ],
  "userinfo_endpoint": base_url + "/userinfo",
  "token_endpoint_auth_signing_alg_values_supported": [
    "RS256"
  ],
  "frontchannel_logout_supported": True,
  "code_challenge_methods_supported": [
    "S256"
  ],
  "jwks_uri": base_url + "/jwks.json",
  "frontchannel_logout_session_supported": True,
  "subject_types_supported": [
    "public",
    "pairwise"
  ],
  "id_token_signing_alg_values_supported": [
    "RS256"
  ],
  "authorization_signing_alg_values_supported": [
    "RS256"
  ]
}

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
        #"authorization_servers": [config('IDP_URL')], # This should be ID-porten, but this application was used during testing.
        "credential_configurations_supported": {
            "eu.europa.ec.eudi.loyalty_mdoc": {
                "claims": {
                    "eu.europa.ec.eudi.loyalty.1": {
                    "client_id": {
                        "display": [
                        {
                            "locale": "en",
                            "name": "Comapny internal client id"
                        }
                        ],
                        "mandatory": True,
                        "value_type": "string"
                    },
                    "company": {
                        "display": [
                        {
                            "locale": "en",
                            "name": "Loyalty card company"
                        }
                        ],
                        "mandatory": True,
                        "value_type": "string"
                    },
                    "expiry_date": {
                        "display": [
                        {
                            "locale": "en",
                            "name": "Alpha-2 country code, representing the nationality of the PID User."
                        }
                        ],
                        "mandatory": True
                    },
                    "family_name": {
                        "display": [
                        {
                            "locale": "en",
                            "name": "Current Family Name"
                        }
                        ],
                        "mandatory": True,
                        "value_type": "string"
                    },
                    "given_name": {
                        "display": [
                        {
                            "locale": "en",
                            "name": "Current First Names"
                        }
                        ],
                        "mandatory": True,
                        "value_type": "string"
                    },
                    "issuance_date": {
                        "display": [
                        {
                            "locale": "en",
                            "name": "Alpha-2 country code, representing the nationality of the PID User."
                        }
                        ],
                        "mandatory": True
                    }
                    }
                },
                "credential_signing_alg_values_supported": [
                    "ES256"
                ],
                "cryptographic_binding_methods_supported": [
                    "jwk",
                    "cose_key"
                ],
                "display": [
                    {
                    "locale": "en",
                    "logo": {
                        "alt_text": "A square figure of a PID",
                        "url": "https://examplestate.com/public/pid.png"
                    },
                    "name": "Loyalty"
                    }
                ],
                "doctype": "eu.europa.ec.eudi.loyalty.1",
                "format": "mso_mdoc",
                "proof_types_supported": {
                    "cwt": {
                    "proof_alg_values_supported": [-7],
                    "proof_crv_values_supported": [1],
                    "proof_signing_alg_values_supported": [
                        "ES256"
                    ]
                    },
                    "jwt": {
                        "proof_signing_alg_values_supported": [
                            "ES256"
                        ]
                    }
                },
                "scope": "eu.europa.ec.eudi.loyalty.1"
            },
        },
    }
    
@router.get("/credential_offer")
async def credential_offer_qr(request: Request):
    """
    Qr code endpoint with a credential offer.
    """
    pre_auth_code = str(uuid.uuid4())
    base_redirect_uri = "openid-credential-offer://?credential_offer="
    qr_code, data = generate_qr_code(base_redirect_uri, create_pre_auth_credential_offer(request, pre_auth_code))
    print(qr_code)
    pre_authorized_codes[pre_auth_code] = {
        "exp": datetime.now() + timedelta(minutes=5),
        "credential_type": "eu.europa.ec.eudi.pid_jwt_vc_json"
    }
    print("Pre-auth-code saved in local storage!")
    return templates.TemplateResponse("qr_code.html", {"request": request, "qr_code": qr_code, "data": data})

@router.post("/token")
async def token(request: Request):
    """
    Token endpoint. The wallet will send a post request to this endpoint, and that will contain a tx code and a pre 
    authorized code. The pre authorized code we will check up against the pre authorized code registered with us. 
    If it matches, it will later (when we have created support for it) return the access token of the logged in user.
    """
    #Fills data with the parameters from the xxx urlencoded content which posts to
    #our endpoint
    body = await request.body()
    body_str = body.decode("utf-8")
    
    print("body raw string: ", body_str)
    
    parsed_query = parse_qs(body_str)
    print("parsed query: ", parsed_query)
    
    tx_code = parsed_query.get("tx_code")[0]
    grant_type = parsed_query.get("grant_type")[0]
    pre_authorized_code = parsed_query.get("pre-authorized_code")[0]
    
    #tx_code = data.get('tx_code')
    print("token endpoint parameters: ", tx_code, " ", grant_type, "", pre_authorized_code)

    #Checks if it is supposed to follow pre-autorized code run.
    if grant_type == "urn:ietf:params:oauth:grant-type:pre-authorized_code" and tx_code == "123456":

        #Gets and sets the parts of the url encoded content.
        #pre_authorized_code = data.get('pre-authorized_code')


        #If the pre autorized code is not same as the one set earlier in credential offer, exception.
        print("pre_authorized_codes: ", pre_authorized_codes)
        if pre_authorized_codes[pre_authorized_code] is None:
            raise HTTPException(status_code=401, detail="Invalid pre-authorized code")

        #Else, it now will now get the access token of the logged in user of idporten.
        token = getLoggedInUsersToken()
        token = "123"
        response = {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 86400,
        }

        #Headers neeed to be this, according to draft 13 oid4vci.
        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-store"
        }

        #Sets headers to the response we will send.

        #Sends the response back so that the wallet gets the id token in return.
        return JSONResponse(content=response, headers=headers)

    #If the grant type is not pre-autorized flow:
    else:
        raise HTTPException(status_code=418, detail="Service only supports pre autorized flow.")

@router.post("/credential")
async def issue_credential(request: Request, x_public_key: Optional[str] = Header(None)):
    PID_DATA = {
        "eu.europa.ec.eudi.loyalty_mdoc": {
            "client_id": "1234",
            # "company": "Digdir",
            # "expiry_date": datetime.now().isoformat(),
            # "family_name": "Normann",
            # "given_name": "Ola",
            # "issuance_date": datetime.now().isoformat(),
        }
    }
    validity = {
        "issuance_date": "2023-08-01",
        "expiry_date": "2069-08-01",
    }
    
    with open("app/keys/private_key.pem", "rb") as file:
        private_key = serialization.load_pem_private_key(file.read(), password=None)
    
    priv_d = private_key.private_numbers().private_value
    
    with open("app/keys/public_key.pem", "rb") as file:
        public_key = serialization.load_pem_public_key(file.read())
    cose_pkey = {
        "KTY": "EC2",
        "CURVE": "P_256",
        "ALG": "ES256",
        "D": priv_d.to_bytes((priv_d.bit_length() + 7) // 8, "big"),
        "KID": b"mdocIssuerPkey",
    }
    public_numbers = public_key.public_numbers()
    x = public_numbers.x
    y = public_numbers.y
    x_bytes = x.to_bytes((x.bit_length() + 7) // 8, byteorder='big')
    y_bytes = y.to_bytes((y.bit_length() + 7) // 8, byteorder='big')
    device_publickey = {
        1: 2,
        -1: 1,
        -2: x_bytes,
        -3: y_bytes,
    }

    mdoci = MdocCborIssuer(private_key=cose_pkey, alg="ES256")
    mdoci.new(
        doctype="eu.europa.ec.eudi.loyalty.1",
        data=PID_DATA,
        validity=validity,
        devicekeyinfo=device_publickey,
        cert_path="app/keys/certificate.pem",
    )

    credential = base64.urlsafe_b64encode(mdoci.dump()).decode("utf-8")
    response = {
        "credential": credential
    }
    
    return JSONResponse(content=response)