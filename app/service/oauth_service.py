from urllib.parse import urlencode, urlunparse


import os

def get_idp_uri() -> str:
    base_url = os.getenv("IDP_URL")
    params = {
        "client_id": os.getenv("CLIENT_ID"),
        "response_type": "code",
        "scope": ["openid", "profile"],
        "redirect_uri": "localhost:8980/",
    }
    
if __name__ == "__main__":
    import dotenv

    dotenv.load_dotenv()
    print(get_idp_uri())