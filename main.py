from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from starlette.config import Config

from app.service.qr_code_service import generate_qr_code

import os

config = Config('.env')

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.add_middleware(SessionMiddleware, secret_key="this is a secret key")


oauth = OAuth()
oauth.register(
    name=config('IDP_NAME'), # idporten
    client_id=config('CLIENT_ID'),
    client_secret=config('CLIENT_SECRET'),
    server_metadata_url=config('IDP_URL') + '/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid profile difitest:guardian'},
)


@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


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

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8980))
    import uvicorn
    uvicorn.run(app, port=port)