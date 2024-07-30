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
from app.service.misc import templates

"""
This file contains the OIDC endpoints for the OID4VCI specification.
"""

router = APIRouter()

config = Config('.env')

# In-memory credential storage (replace with a database in production)
credentials: Dict[str, VerifiableCredential] = {}
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
    return {
  "request_parameter_supported": False,
  "pushed_authorization_request_endpoint": config('IDP_URL') + "/par",
  "authorization_response_iss_parameter_supported": True,
  "introspection_endpoint": config('IDP_URL') + "/token/introspect",
  "claims_parameter_supported": False,
  "scopes_supported": [
    "openid",
    "profile"
  ],
  "issuer": config('IDP_URL') + "",
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
  "token_endpoint": config('IDP_URL') + "/token",
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
  "revocation_endpoint": config('IDP_URL') + "/token/revoke",
  "prompt_values_supported": [
    "consent",
    "login",
    "none"
  ],
  "userinfo_endpoint": config('IDP_URL') + "/userinfo",
  "token_endpoint_auth_signing_alg_values_supported": [
    "RS256"
  ],
  "frontchannel_logout_supported": True,
  "code_challenge_methods_supported": [
    "S256"
  ],
  "jwks_uri": config('IDP_URL') + "/jwks.json",
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
    # "authorization_servers": [config('IDP_URL')],
    return {
        "credential_issuer": base_url,
        "credential_endpoint": f"{base_url}/credential",
        #"authorization_servers": [config('IDP_URL')],
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

    {
        "credential_issuer": base_url,
        "credential_endpoint": f"{base_url}/credential",
        "credential_configurations_supported": {
            # "eu.europa.ec.eudi.pid_jwt_vc_json": {
            #     "claims": {
            #         "ward_pid_number": {
            #             "display": [
            #             {
            #                 "locale": "en",
            #                 "name": "PID of the ward"
            #             }
            #             ],
            #             "mandatory": False
            #         },
            #         "user_pid": {
            #             "display": [
            #             {
            #                 "locale": "en",
            #                 "name": "PID of user"
            #             }
            #             ],
            #             "mandatory": False
            #         }
            #     },
            #     "display": [
            #         {
            #             "locale": "en",
            #             "logo": {
            #             "alt_text": "A square figure of a PID",
            #             "url": ""
            #             },
            #             "name": "PID"
            #         }
            #     ],
            #     "types": ["VerifiableCredential", "WardCredential"],
            #     "format": "vc+sd-jwt",
            #     "scope": "eu.europa.ec.eudi.pid.1", # Skjønner ikke helt.
            #     "vct": "eu.europa.ec.eudi.pid_jwt_vc_json"
            # },
            "eu.europa.ec.eudi.ward_mdoc": {
                "claims": {
                    "eu.europa.ec.eudi.ward.1": {
                        "client_id": {
                            "display": [
                            {
                                "locale": "en",
                                "name": "Comapny internal client id"
                            }
                            ],
                            "mandatory": False,
                            "value_type": "string"
                        },
                        "company": {
                            "display": [
                            {
                                "locale": "en",
                                "name": "Loyalty card company"
                            }
                            ],
                            "mandatory": False,
                            "value_type": "string"
                        },
                    },
                },
            },
            # "credential_signing_alg_values_supported": [
            #     "ES256"
            # ],
            # "cryptographic_binding_methods_supported": [
            #     "jwk",
            #     "cose_key"
            # ],
            # "display": [
            #         {
            #             "locale": "en",
            #             "logo": {
            #             "alt_text": "A square figure of a PID",
            #             "url": ""
            #             },
            #             "name": "PID"
            #         }
            #     ],
            "doctype": "eu.europa.ec.eudi.ward.1",
            "format": "mso_mdoc",
            # "proof_types_supported": {
            #     "cwt": {
            #         "proof_alg_values_supported": [-7],
            #         "proof_crv_values_supported": [1],
            #         "proof_signing_alg_values_supported": [
            #             "ES256"
            #         ]
            #     },
            #     "jwt": {
            #         "proof_signing_alg_values_supported": [
            #             "ES256"
            #         ]
            #     }
            # },
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

"""
Token endpoint. The wallet till send a post request to this endpoint, and that will contain a tx code and a pre 
authorized code. The pre authorized code we will check up against the pre authorized code registered with us. 
If it matches, it will later (when we have created support for it) return the access token of the logged in user.
"""
@router.post("/token")
def token(request:Request):
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
    else:
        raise HTTPException(status_code=418, detail="Service only supports pre autorized flow.")



# TODO: this
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
