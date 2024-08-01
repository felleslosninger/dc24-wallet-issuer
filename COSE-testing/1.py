import os

from pymdoccbor.mdoc.issuer import MdocCborIssuer
from datetime import datetime

PKEY = {
    'KTY': 'EC2',
    'CURVE': 'P_256',
    'ALG': 'ES256',
    'D': os.urandom(32),
    'KID': b"demo-kid"
}

PUBKEY = {
    'KTY': 'EC2',
    'CURVE': 'P_256',
    'ALG': 'ES256',
    'D': os.urandom(32),
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

mdoc = mdoci.new(
    doctype="eu.europa.ec.eudi.loyalty.1",
    data=PID_DATA,
    devicekeyinfo=PUBKEY  # TODO
)

mdoc

mdoci.dump()

mdoci.dumps()

print(mdoc)

print(mdoci.dumps())
print(mdoci.dump())
import base64
print()
print(base64.urlsafe_b64encode(mdoci.dump()).decode('utf-8'))