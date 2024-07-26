# main.py

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

app = FastAPI()

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=uuid.uuid4())

# Configure OAuth
config = Config('.env')
oauth = OAuth(config)

oauth.register(
    name=config('IDP_NAME'), # idporten
    client_id=config('CLIENT_ID'),
    client_secret=config('CLIENT_SECRET'),
    server_metadata_url=config('IDP_URL') + '/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid profile difitest:guardian'},
)

# OAuth2 scheme for credential issuance
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="auth",
    tokenUrl="token"
)



# In-memory credential storage (replace with a database in production)
credentials: Dict[str, VerifiableCredential] = {}
pre_authorized_codes: Dict[str, Dict] = {}

ISSUER_DID = "did:example:123456789abcdefghi"

@app.get("/.well-known/openid-credential-issuer")
async def credential_issuer_metadata():
    return {
        "issuer": ISSUER_DID,
        "authorization_endpoint": "https://example.com/auth",
        "token_endpoint": "https://example.com/token",
        "credential_endpoint": "https://example.com/credential",
        "jwks_uri": "https://example.com/jwks",
        "credential_types_supported": ["VerifiableCredential", "ProfileCredential"],
        "credentials_supported": {
            "ProfileCredential": {
                "types": ["VerifiableCredential", "ProfileCredential"],
                "format": "jwt_vc",
            }
        },
    }

@app.post("/credential-offer")
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

@app.post("/token")
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

@app.post("/credential")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)