# EU ISSUER

## How to run

Make sure you have python installed.


### Normal application run
```bash
pip3 install -r requirements.txt
python3 main.py
```

### Development mode
The application will update automactially when code is changed when using the ```--reload``` flag
```bash
pip3 install -r requirements.txt
python3 -m uvicorn main:app --reload --port 8980
```

## Endpoint documentation

Endpoint documentation can be found at ```localhost:8980/docs```

## Requirements.txt

To update the ```requirements.txt``` file with new libraries, a virtual environment has to be used.
```bash
python3 -m venv .venv
```
### Activate avirtual environment on Mac/linux
```bash
source .venv/bin/activate
```
### Activate avirtual environment on Windows
```bash
.\.env\Scripts\activate
```
### Deactivate virtual environment
```bash
deactivate
```
### Update the requirements.txt file
When the virtual environment is activated, run this command to update the ```requirements.txt``` file.
```bash
pip3 freeze > requirements.txt
```

