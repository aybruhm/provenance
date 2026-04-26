import hashlib
import hmac
import secrets


def hash_api_key(api_key: str) -> str:
    """
    Deterministic SHA-256 of an API key (canonical sort, no whitespace).

    Args:
        api_key: The API key string to hash.
    """

    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key(env: str = "live") -> tuple[str, str, str]:
    """
    Generate a new API key.

    Args:
        env: The environment prefix to use (e.g. "live", "test").
    """

    key_body = secrets.token_urlsafe(32)
    full_key = f"pk_{env}_{key_body}"
    prefix = f"pk_{env}_{key_body[:8]}"
    key_hash = hash_api_key(api_key=full_key)
    return full_key, prefix, key_hash


def verify_api_key(incoming_key: str, stored_hash: str) -> bool:
    """
    Verify an incoming API key against a stored hash.

    Args:
        incoming_key: The API key string to verify.
        stored_hash: The stored hash to compare against.
    """

    computed = hash_api_key(api_key=incoming_key)
    return hmac.compare_digest(computed, stored_hash)
