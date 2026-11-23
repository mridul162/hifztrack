from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

password_hasher = PasswordHasher()

# A valid hash keeps the unknown-email login path close in cost to a real-user path.
DUMMY_PASSWORD_HASH = "$argon2id$v=19$m=65536,t=3,p=4$0TIPmdPQVElYF22M47zqjg$5RRkuq9Qx5tVvIqYvWCfZ14YCsT8nfCpTUCB5kBlln0"


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
