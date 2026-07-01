"""Content hashing for SeeYou contest_file rows."""
import base64
import hashlib


def content_hash(data: bytes) -> str:
    return base64.b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")
