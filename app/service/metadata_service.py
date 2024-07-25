import requests
import os
import json

"""
This file is responsible for fetching metadata from the identity provider.
"""


def get_idp_metadata() -> dict:
    """
    Gets metadata from the identity provider.
    """
    IDP_url = os.getenv("IDP_URL") + "/.well-known/openid-configuration"
    return requests.get(IDP_url).json()


def get_issuer_metadata() -> dict:
    """
    Gets the metadata from this application
    """
    with open("app/config/metadata.json") as f:
        return json.load(f)
    
if __name__ == "__main__":
    import dotenv

    dotenv.load_dotenv()
    print(get_idp_metadata())
