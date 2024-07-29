
from app.service.misc import get_base_url
from fastapi import Request


def create_pre_auth_credential(request: Request):
    return {
        "credential_issuer": get_base_url(request),
        "credential_configuration_ids": [
            "eu.europa.ec.eudi.pid_jwt_vc_json"
        ],
        "grants": {
            "urn:ietf:params:oauth:grant-type:pre-authorized_code": {
                "pre-authorized_code": "oaKazRN8I0IbtZ0C7JuMn5",
            }
        }
        }