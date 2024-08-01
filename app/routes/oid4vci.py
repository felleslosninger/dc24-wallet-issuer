from starlette.config import Config
from fastapi import APIRouter, Request
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from fastapi.templating import Jinja2Templates
from urllib.parse import parse_qs
from pymdoccbor.mdoc.issuer import MdocCborIssuer

import os
import uuid
import base64
from typing import Dict
from datetime import datetime, timedelta

from app.routes.oauth import getLoggedInUsersToken
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
Token endpoint. The wallet will send a post request to this endpoint, and that will contain a tx code and a pre 
authorized code. The pre authorized code we will check up against the pre authorized code registered with us. 
If it matches, it will later (when we have created support for it) return the access token of the logged in user.
"""
@router.post("/token")
async def token(request: Request):
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
async def issue_credential(request: Request):
    
    PKEY = {
    'KTY': 'EC2',
    'CURVE': 'P_256',
    'ALG': 'ES256',
    'D': os.urandom(32),
    'KID': b"test-kid"
    }

    PID_DATA = {
        "eu.europa.ec.eudi.loyalty_mdoc": {
            "client_id": "1234",
            "company": "Digdir",
            "expiry_date": datetime.now().isoformat(),
            "family_name": "Normann",
            "given_name": "Ola",
            "issuance_date": datetime.now().isoformat(),
        }
    }

    mdoci = MdocCborIssuer(
        private_key=PKEY
    )

    mdoci.new(
        doctype="eu.europa.ec.eudi.loyalty.1",
        data=PID_DATA,
        devicekeyinfo=PKEY  # TODO
    )

    credential = base64.urlsafe_b64encode(mdoci.dump()).decode('utf-8')
    credential = "ompuYW1lU3BhY2VzoXgeZXUuZXVyb3BhLmVjLmV1ZGkubG95YWx0eV9tZG9jhtgYoQCkaGRpZ2VzdElEAGZyYW5kb21YIMeagLMhnPa-HTirIfZlF7tLKWClrHb9GEBJPJt_vNV4cWVsZW1lbnRJZGVudGlmaWVya2ZhbWlseV9uYW1lbGVsZW1lbnRWYWx1ZWdOb3JtYW5u2BihAaRoZGlnZXN0SUQBZnJhbmRvbVggdQ0uYOzTR8DgG0komN2T4EIEtdbdXOBfiYwKWOlyhA9xZWxlbWVudElkZW50aWZpZXJqZ2l2ZW5fbmFtZWxlbGVtZW50VmFsdWVjT2xh2BihAqRoZGlnZXN0SUQCZnJhbmRvbVgg60urgM0NYcfIp30aPQlfJquUf55noaNG2Ul7XCPfe5hxZWxlbWVudElkZW50aWZpZXJnY29tcGFueWxlbGVtZW50VmFsdWVmRGlnZGly2BihA6RoZGlnZXN0SUQDZnJhbmRvbVgg-dq0_Cnvh3rrUJGq-nA5It4LwDIkEVXVZs4FMULxaclxZWxlbWVudElkZW50aWZpZXJpY2xpZW50X2lkbGVsZW1lbnRWYWx1ZWQxMjM02BihBKRoZGlnZXN0SUQEZnJhbmRvbVgg6F1OB5a5ouy18yjsRoneyNz0drS3_s5_V-Ky7CahKH1xZWxlbWVudElkZW50aWZpZXJtaXNzdWFuY2VfZGF0ZWxlbGVtZW50VmFsdWV4GjIwMjQtMDgtMDFUMTI6MTI6NTkuNzY4MzAz2BihBaRoZGlnZXN0SUQFZnJhbmRvbVggmDex3uaME7xH7lUmQ5TAXtc-ZXDbwtplSiLoR-y45q5xZWxlbWVudElkZW50aWZpZXJrZXhwaXJ5X2RhdGVsZWxlbWVudFZhbHVl2QPseBoyMDI0LTA4LTAxVDEyOjEyOjU5Ljc2ODI5M2ppc3N1ZXJBdXRoWQQ-0oRNogEmBEhkZW1vLWtpZKEYIVkCDTCCAgkwggGvoAMCAQICFGzOGK_NxORUbzVtxz0t5YKY1T2uMAoGCCqGSM49BAMCMGQxCzAJBgNVBAYTAlVTMRMwEQYDVQQIDApDYWxpZm9ybmlhMRYwFAYDVQQHDA1TYW4gRnJhbmNpc2NvMRMwEQYDVQQKDApNeSBDb21wYW55MRMwEQYDVQQDDApteXNpdGUuY29tMB4XDTI0MDgwMTEwMTI1OVoXDTI0MDgxMTEwMTI1OVowZDELMAkGA1UEBhMCVVMxEzARBgNVBAgMCkNhbGlmb3JuaWExFjAUBgNVBAcMDVNhbiBGcmFuY2lzY28xEzARBgNVBAoMCk15IENvbXBhbnkxEzARBgNVBAMMCm15c2l0ZS5jb20wWTATBgcqhkjOPQIBBggqhkjOPQMBBwNCAAR67jfrRjSprUbP5n52cIxF6m3tR39NzSLEByOTF6dRYvr-hzWoQN4d1Xb6K2lzBplTDFezyOHvucyJOwWzNsizoz8wPTA7BgNVHREENDAyhjBodHRwczovL2NyZWRlbnRpYWwtaXNzdWVyLm9pZGMtZmVkZXJhdGlvbi5vbmxpbmUwCgYIKoZIzj0EAwIDSAAwRQIgZSYO1F_oDeVEuYNwr5pIEWrD3T8xSoiFxMR2kdXFhGQCIQC2dNtcJsHqy_6BTrgrLbXQxVyuz9oiEdjTMuCNg2dT41kB1qZndmVyc2lvbmMxLjBvZGlnZXN0QWxnb3JpdGhtZnNoYTI1Nmx2YWx1ZURpZ2VzdHOheB5ldS5ldXJvcGEuZWMuZXVkaS5sb3lhbHR5X21kb2OmAFggh0_vP85EoZru577t1qKZlHxdQeLGi0IbQwMg3KOLv28BWCAzDtxW9FohkHzDQSfdgACp1u5owrpazSyYj3_ectIy-gJYIGaSNIwY9oq76j9cjzGwrrb4NmDI-RmeOkz5yWHB_eIhA1ggXvFhVOfr180ETbK-2Dlv9hyTVPFCUi4pme55UMXCskMEWCBG9b9a2BCAAgjYKzV9x74kYLhqMHsfXqzKd35GYu9tAQVYIC848yg8xYdY4ys9fn1ZEg1WqFSojkGVlQCCwRmCEF0PbWRldmljZUtleUluZm-haWRldmljZUtlefZnZG9jVHlwZXgeZXUuZXVyb3BhLmVjLmV1ZGkubG95YWx0eV9tZG9jbHZhbGlkaXR5SW5mb6Nmc2lnbmVkVsB0MjAyNC0wOC0wMVQxMDoxMjo1OVppdmFsaWRGcm9tVsB0MjAyNC0wOC0wMVQxMDoxMjo1OVpqdmFsaWRVbnRpbFbAdDIwMjktMDctMzFUMTA6MTI6NTlaWEB4MfB4w6h3yRWYAHFgpuXDMmNBeShV8-xRV_ywPCZFBmtj7T8pZleJUkQOFTM2PjeBf2oW4iAtga6VYyNYXqys"
    response = {
        "credential": credential
    }
    
    print("Credential: ", credential)
        
    return JSONResponse(content=response)