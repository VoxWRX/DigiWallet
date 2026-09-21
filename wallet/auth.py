import binascii
import hashlib
import hmac
import os

_ITERATIONS = 200_000


def make_password(password):
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return binascii.hexlify(dk).decode(), binascii.hexlify(salt).decode()


def verify_password(password, pw_hash, salt_hex):
    try:
        salt = binascii.unhexlify(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
        return hmac.compare_digest(binascii.hexlify(dk).decode(), pw_hash)
    except Exception:
        return False