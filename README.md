# EU ISSUER

## How to run

Make sure you have python installed.

```
pip3 install -r requirements.txt
uvicorn main:app --reload --port 8980
```

## Endpoint documentation

Endpoint documentation can be found at ```localhost:8980/docs```

## Requirements.txt

To update the ```requirements.txt``` file with new libraries, a virtual environment has to be used.
```
python -m venv .venv
```
### Activate avirtual environment on Mac/linux
```
source .venv/bin/activate
```
### Activate avirtual environment on Windows
```
.\.env\Scripts\activate
```
### Deactivate virtual environment
```
deactivate
```
### Update the requirements.txt file
When the virtual environment is activated, run this command to update the ```requirements.txt``` file.
```
pip3 freeze > requirements.txt
```

