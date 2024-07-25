from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request

from app.service.metadata_service import get_idp_metadata
from app.service.qr_code_service import generate_qr_code

load_dotenv()

app = FastAPI()

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/metadata")
async def get_metadata_route():
    return get_idp_metadata()


@app.get("/issue")
async def get_credentials(request: Request):
    metadata: dict = get_idp_metadata()

    generate_qr_code("test")
