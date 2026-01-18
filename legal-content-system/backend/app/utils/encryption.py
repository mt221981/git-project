"""Encryption utilities for sensitive data."""

from cryptography.fernet import Fernet
from app.config import settings
import base64
import hashlib


def get_encryption_key() -> bytes:
    """
    Derive encryption key from SECRET_KEY.

    Returns:
        Fernet-compatible encryption key
    """
    # Use SECRET_KEY to derive a consistent Fernet key
    key_material = settings.SECRET_KEY.encode('utf-8')
    # Hash to get 32 bytes, then base64 encode for Fernet
    hashed = hashlib.sha256(key_material).digest()
    return base64.urlsafe_b64encode(hashed)


def encrypt_text(plaintext: str) -> str:
    """
    Encrypt text using Fernet symmetric encryption.

    Args:
        plaintext: Text to encrypt

    Returns:
        Encrypted text as string

    Example:
        >>> encrypted = encrypt_text("my_password")
        >>> decrypted = decrypt_text(encrypted)
        >>> assert decrypted == "my_password"
    """
    if not plaintext:
        return ""

    key = get_encryption_key()
    f = Fernet(key)

    encrypted_bytes = f.encrypt(plaintext.encode('utf-8'))
    return encrypted_bytes.decode('utf-8')


def decrypt_text(encrypted_text: str) -> str:
    """
    Decrypt text encrypted with encrypt_text.

    Args:
        encrypted_text: Encrypted text string

    Returns:
        Decrypted plaintext

    Raises:
        Exception: If decryption fails (wrong key or corrupted data)
    """
    if not encrypted_text:
        return ""

    key = get_encryption_key()
    f = Fernet(key)

    try:
        decrypted_bytes = f.decrypt(encrypted_text.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        raise Exception(f"Decryption failed: {str(e)}")
