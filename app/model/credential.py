from pydantic import BaseModel
from typing import List

class CredentialSubject(BaseModel):
    pid: str
    guardian_pid: str
    ward_pid: str

class VerifiableCredential(BaseModel):
    id: str
    type: List[str]
    issuer: str
    issuanceDate: str
    credentialSubject: CredentialSubject