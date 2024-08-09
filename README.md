# EU ISSUER

This is an application for issuing verifiable credentials to the [EUDIW (EU Digital Identity Wallet) reference implementation](https://github.com/eu-digital-identity-wallet/eudi-app-android-wallet-ui). Currently, this application can communicate with the EUDIW to issue credentials, but an error is thrown from the wallet when trying to save the verifiable credential. More info in [Future work](#future-work).

To test out credential issuance yourself, launch the application and go to https://0.0.0.0:8980/credential_offer.

This application can be found on https://wallet.svedal.eu, but this website will probably disappear in the future.

### Table of Contents

1. [How to run](#how-to-run)
   - [Setup certificates](#setup-certificates)
   - [Install libraries](#install-libraries)
   - [Normal application run](#normal-application-run)
   - [Development mode](#development-mode)
2. [Endpoint documentation](#endpoint-documentation)
3. [Requirements.txt](#requirementstxt)
   - [Activate a virtual environment on Mac/Linux](#activate-a-virtual-environment-on-maclinux)
   - [Activate a virtual environment on Windows](#activate-a-virtual-environment-on-windows)
   - [Deactivate virtual environment](#deactivate-virtual-environment)
   - [Update the requirements.txt file](#update-the-requirementstxt-file)
4. [Future work](#future-work)

# How to run

The first step is to make sure you have Python 3.12 installed.

## Setup certificates

The ```generate_certificate.py``` script automatically creates the required certificates for running this application.
This only needs to be done once.
To run the script, write this in your terminal:
```bash
python3 generate_certificate.py
```

## Install libraries

The easiest way to install the libraries needed for this project is to use this command:
```bash
pip3 install -r requirements.txt
```
This action is only needed once.

## Normal application run
To run the application, use this command: 
```bash
python3 main.py
```

## Development mode
The application will update automatically when code is changed while using the ```--reload``` flag.
```bash
python3 -m uvicorn main:app --reload --port 8980
```

# Endpoint documentation

Endpoint documentation can be found at ```localhost:8980/docs```

# Requirements.txt

To update the ```requirements.txt``` file with new libraries, a virtual environment has to be used.
```bash
python3 -m venv .venv
```
## Activate a virtual environment on Mac/linux
```bash
source .venv/bin/activate
```
## Activate a virtual environment on Windows
```bash
.\.env\Scripts\activate
```
## Deactivate virtual environment
```bash
deactivate
```
### Update the requirements.txt file
When the virtual environment is activated, run this command to update the ```requirements.txt``` file.
```bash
pip3 freeze > requirements.txt
```

# Future work

Here is a list of work that needs to be done to make this application usable:

1. __Add correct device_key:__ As of now, the public key of the MSO (Mobile security object) is set as the public key of the certificate that is used for signing the COSE message with the credentials.
The EUDIW complains that the public key in the MSO should be the same key as the one in the wallet.
There is no documentation about how to get the device key from the EUDIW (EU Digital Identity Wallet), but it is possible to turn off this check in the document manager dependency in EUDIW.
The [EU reference implementation](https://github.com/eu-digital-identity-wallet/eudi-srv-web-issuing-eudiw-py) of the python issuer gets the device key from a header in the ``/cbor``endpoint. 
2. __Refactor ``oid4vci.py``__: As of now, all the json fields are pasted directly in this file. THis was a temporary solution during testing, and the contents of the enpoints should be split into multiple parts.
3. __Frontend__: THe frontend is just temporary. The user should be redirected to the QR code after being signed in.
4. __Use the IDP as authentication server__: The issuer (this application) is currently used as the authentication server. During production the IDP (Identity provider, i.e. ID-porten) should be used as the authentication provider.
5. __Generate a random TX_code__: Create a transaction code and show it to the user when they scan the QR. The code is currently hardcoded to "123456".
6. __``/credential`` endpoint__: The credential endpoint only gives out credentials with hardcoded test values, but should contain information from the IDP.

# EUDIW notes

To be able to use EUDIW, the app has to be correctly set up. In the wallet's wiki folder there is documentation about how to allow self-signed certificates, which is what this issuer is using.