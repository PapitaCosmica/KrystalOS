import os
from cryptography.fernet import Fernet

def get_encryption_key():
    """
    Retrieves or generates a master encryption key (AES-128 equivalent in Fernet).
    Used for encrypting sensitive documents/signatures at rest.
    """
    key_file = os.path.join(os.getcwd(), "core", "security", "master.key")
    
    if os.path.exists(key_file):
        with open(key_file, "rb") as f:
            return f.read()
    else:
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        key = Fernet.generate_key()
        with open(key_file, "wb") as f:
            f.write(key)
        return key

cipher_suite = Fernet(get_encryption_key())

def encrypt_data(data: bytes) -> bytes:
    return cipher_suite.encrypt(data)

def decrypt_data(data: bytes) -> bytes:
    return cipher_suite.decrypt(data)
