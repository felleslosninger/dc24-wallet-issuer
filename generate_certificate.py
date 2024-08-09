from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.kdf.concatkdf import ConcatKDFHash
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import datetime
import os

"""
This file is responsible for generating a self-signed certificate and private key.
"""

def generate_keys():
    # Generate private key
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())

    # Generate public key
    public_key = private_key.public_key()

    # Generate a self-signed certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"NO"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Vestland"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"Leikanger"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Digdir"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"digdir.no"),
    ])
    certificate = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        public_key
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName(u"localhost"), 
            x509.DNSName(u"dc24-wallet-issuer.fly.dev"), 
            x509.DNSName(u"10.170.204.17")
        ]),
        critical=False,
    ).sign(private_key, hashes.SHA256(), default_backend())

    # Save private key and certificate to files
    os.makedirs("app/keys", exist_ok=True)

    with open("app/keys/private_key.pem", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    with open("app/keys/certificate.pem", "wb") as f:
        f.write(certificate.public_bytes(serialization.Encoding.PEM))

    # Create a .p12 file (PKCS#12)
    p12_password = b"your_password"  # Use a strong password for encryption
    p12 = serialization.pkcs12.serialize_key_and_certificates(
        b"My CA Certificate", 
        private_key, 
        certificate, 
        None,  # No additional certificates
        serialization.BestAvailableEncryption(p12_password)
    )

    # Save the .p12 file
    with open("app/keys/ca-cert.p12", "wb") as f:
        f.write(p12)

    public_numbers = public_key.public_numbers()
    x = public_numbers.x
    y = public_numbers.y

    print(f"x: {x}")
    print(f"y: {y}")
    
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Save the public key to a file
    with open('app/keys/public_key.pem', 'wb') as f:
        f.write(pem)
    
if __name__ == "__main__":
    generate_keys()