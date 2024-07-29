from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from fastapi import APIRouter, Request

"""
This file contains the endpoints for logging in to the IDP (Identity Provider) and getting the user's information.
"""

token = ""

router = APIRouter()

config = Config('.env')

oauth = OAuth()
oauth.register(
    name=config('IDP_NAME'), # idporten
    client_id=config('CLIENT_ID'),
    client_secret=config('CLIENT_SECRET'),
    server_metadata_url=config('IDP_URL') + '/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid profile difitest:guardian'},
)

@router.get('/login')
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    print(redirect_uri)
    return await oauth.idporten.authorize_redirect(request, redirect_uri)


@router.get('/login/oauth2/code/testclient')
async def auth(request: Request):
    token = await oauth.idporten.authorize_access_token(request)
    print("User token: ", token)
    user = token['userinfo']
    return user

def getLoggedInUsersToken():
    return token