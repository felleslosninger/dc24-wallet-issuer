from binascii import unhexlify, hexlify

from pycose.messages import Sign1Message
from pycose.keys import CoseKey
from pycose.headers import Algorithm, KID
from pycose.algorithms import EdDSA, Es256
from pycose.keys.curves import Ed25519
from pycose.keys.keyparam import KpKty, OKPKpD, OKPKpX, KpKeyOps, OKPKpCurve
from pycose.keys.keytype import KtyOKP
from pycose.keys.keyops import SignOp, VerifyOp

import cbor2

message = {
    "issuerAuth": "test"
}

msg = Sign1Message(
    phdr = {Algorithm: Es256, KID: b'kid2'},
    payload = cbor2.dumps(message)
)

print(msg)


cose_key = {
    KpKty: KtyOKP,
    OKPKpCurve: Ed25519,
    KpKeyOps: [SignOp, VerifyOp],
    OKPKpD: unhexlify(b'9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60'),
    OKPKpX: unhexlify(b'd75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a')
}

cose_key = CoseKey.from_dict(cose_key)
print(cose_key)

msg.key = cose_key
# the encode() function performs the signing automatically
encoded = msg.encode()
print(hexlify(encoded))
b'd28449a2012704446b696432a04e7369676e6564206d6573736167655840cc87665ffd3fa33d96f3b606fcedeaef839423221872d0bfa196e069a189a607c2284924c3abb80e942466cd300cc5d18fe4e5ea1f3ebdb62ef8419109447d03'

# decode and verify the signature
decoded = Sign1Message.decode(encoded)
print(decoded)

decoded.key = cose_key
print(decoded.verify_signature())


print(decoded.payload)