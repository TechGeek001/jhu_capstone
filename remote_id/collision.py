import hashlib
import ecdsa
import os

def find_collision(hash, length):
    small = hash[0:length]
    while(True):
        ODID_data = bytearray(os.urandom(160))
        m = hashlib.sha256()
        m.update(ODID_data)
        ODID_hash = m.digest()
        ODID_hash_small = ODID_hash[0:length]
        if (small == ODID_hash_small):
            return ODID_data


ODID_data = bytearray(os.urandom(160))

m = hashlib.sha256()
m.update(ODID_data)
ODID_hash = m.digest()
print(ODID_data)

# sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1, hashfunc=hashlib.sha256) # The default is sha1
# vk = sk.get_verifying_key()
# sig = sk.sign(ODID_hash_small)
# print(vk.verify(sig, ODID_hash_small))

length = 1
while True:
    print(length)
    print(find_collision(ODID_hash, length))
    length += 1

