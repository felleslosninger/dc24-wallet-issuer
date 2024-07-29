from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from starlette.middleware.sessions import SessionMiddleware
from starlette.config import Config

from app.routes import oauth, oid4vci
from app.service.misc import templates

import os

config = Config('.env')
app = FastAPI()
app.include_router(oauth.router)
app.include_router(oid4vci.router)
app.add_middleware(SessionMiddleware, secret_key="this is a secret key")

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """
    Home page of the application. This is a simple page with a login button.
    """
    return templates.TemplateResponse("home.html", {"request": request})



if __name__ == "__main__":
    port = int(os.getenv("PORT", 8980))
    import uvicorn
    uvicorn.run(app, port=port)