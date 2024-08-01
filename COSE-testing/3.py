from pymdoccbor.mdoc.issuer import MdocCborIssuer
import os
from cryptography.hazmat.primitives import serialization


PID_DATA = {
        "eu.europa.ec.eudiw.pid.1": {
            "family_name": "Raffaello",
            "given_name": "Mascetti",
            "birth_date": "1922-03-13"
        }
    }
PKEY = {
    'KTY': 'EC2',
    'CURVE': 'P_256',
    'ALG': 'ES256',
    'D': os.urandom(32),
    'KID': b"demo-kid"
}

# from pymdoccbor.mdoc.issuer import MdocCborIssuer
# from pymdoccbor.mdoc.verifier import MdocCbor
# from pymdoccbor.mso.issuer import MsoIssuer
# import cbor2


# mdoci = MdocCborIssuer(
#         private_key=PKEY
#     )
# mdoc = mdoci.new(
#         doctype="eu.europa.ec.eudiw.pid.1",
#         data=PID_DATA,
#         devicekeyinfo=PKEY  # TODO
#     )

# mdocp = MdocCbor()
# aa = cbor2.dumps(mdoc)
# mdocp.loads(aa)
# mdocp.verify()

# print(mdoc)

#with open("app/keys/")

# cose_pkey = {
#         "KTY": "EC2",
#         "CURVE": "P_256",
#         "ALG": "ES256",
#         "D": priv_d.to_bytes((priv_d.bit_length() + 7) // 8, "big"),
#         "KID": b"mdocIssuer",
#     }




with open("app/keys/private.key", "rb") as key_file:
        private_key = serialization.load_pem_private_key(key_file.read(), password=None)
        
priv_d = private_key.private_numbers().private_value

with open("app/keys/public.key", "rb") as public_key_file:
        public_key = serialization.load_pem_public_key(public_key_file.read())
        
print("public key: ", public_key)
cose_pkey = {
        "KTY": "EC2",
        "CURVE": "P_256",
        "ALG": "ES256",
        "D": priv_d.to_bytes((priv_d.bit_length() + 7) // 8, "big"),
        "KID": b"mdocIssuer",
    }

# Construct and sign the mdoc
mdoci = MdocCborIssuer(private_key=cose_pkey, alg="ES256")
validity = {
        "issuance_date": "2022-03-13",
        "expiry_date": "2030-03-13"
    }
from cryptography import x509
import ssl

# with open('app/keys/certificate.der', 'rb') as cert_file:
#     cert_data = cert_file.read()
# cert = x509.load_der_x509_certificate(cert_data)
# print(cert)

mdoci.new(
    doctype="eu.europa.ec.eudi.loyalty.1",
    data=PID_DATA,
    validity=validity,
    devicekeyinfo=public_key,
    cert_path="app/keys/certificate.der",
)

import base64
print(base64.urlsafe_b64encode(mdoci.dump()).decode("utf-8"))