import cbor2
from cwt import COSE
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes

def generate_key_pair():
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    return private_key, public_key

def create_signed_cbor(message, issuer_auth, private_key):
    # Create the payload
    payload = {
        'message': message,
        'issuerAuth': issuer_auth
    }

    # Encode the payload as CBOR
    payload_cbor = cbor2.dumps(payload)

    # Create a COSE_Sign1 message
    cose_key = {
        'kty': 'EC',
        'crv': 'P-256',
        'd': private_key.private_numbers().private_value.to_bytes(32, 'big')
    }

    cose = COSE.new()
    signed_cose = cose.encode_and_sign(
        payload_cbor,
        key=cose_key,
        protected={'alg': 'ES256'}
    )

    return signed_cose

def main():
    message = "Hello, CBOR and COSE!"
    issuer_auth = "ExampleIssuerAuth123"

    # Generate key pair
    private_key, public_key = generate_key_pair()

    # Create signed CBOR
    signed_cbor = create_signed_cbor(message, issuer_auth, private_key)

    print("Signed CBOR (hex):", signed_cbor.hex())

    # Verification (optional, for demonstration)
    cose = COSE.new()
    cose_key = {
        'kty': 'EC',
        'crv': 'P-256',
        'x': public_key.public_numbers().x.to_bytes(32, 'big'),
        'y': public_key.public_numbers().y.to_bytes(32, 'big')
    }
    decoded = cose.decode(signed_cbor, key=cose_key)
    print("Decoded payload:", cbor2.loads(decoded))

if __name__ == "__main__":
    main()