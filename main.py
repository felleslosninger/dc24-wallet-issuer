from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware


from app.service.metadata_service import get_idp_metadata
from app.service.qr_code_service import generate_qr_code

import os

load_dotenv()

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.add_middleware(SessionMiddleware, secret_key="this is a secret key")


idporten_metadata = get_idp_metadata()
oauth = OAuth()
oauth.register(
    name='idporten',
    client_id=os.getenv('CLIENT_ID'),
    client_secret=os.getenv('CLIENT_SECRET'),
    server_metadata_url=os.getenv('IDP_URL') + '/.well-known/openid-configuration',
    redirect_uri=None,
    client_kwargs={'scope': 'openid profile difitest:guardian'},
)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/metadata")
async def get_metadata_route():
    return get_idp_metadata()

@app.get('/login')
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    print(redirect_uri)
    return await oauth.idporten.authorize_redirect(request, redirect_uri)

@app.get('/login/oauth2/code/testclient')
async def auth(request: Request):
    token = await oauth.idporten.authorize_access_token(request)
    print("token", token)
    user = token['userinfo']
    return user



@app.get("/issue")
async def get_credentials(request: Request):
    metadata: dict = get_idp_metadata()

    generate_qr_code("test")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8980))
    import uvicorn
    uvicorn.run(app, port=port)