# EU ISSUER

This is an application for issuing verifiable credentials to the [EUIDW (EU Digital Identity Wallet) reference implementation](https://github.com/eu-digital-identity-wallet/eudi-app-android-wallet-ui).

# How to run

THe first step is to make sure you have python 3.12 installed.

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
The application will update automactially when code is changed while using the ```--reload``` flag.
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
## Activate avirtual environment on Mac/linux
```bash
source .venv/bin/activate
```
## Activate avirtual environment on Windows
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

1. 