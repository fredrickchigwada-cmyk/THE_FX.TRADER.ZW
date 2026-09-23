import base64
import hashlib
import secrets
import string


def generate_verifier():
    alphabet = string.ascii_letters + string.digits + "-._~"
    return "".join(secrets.choice(alphabet) for _ in range(64))


def challenge_from_verifier(verifier):
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def generate_state():
    return secrets.token_urlsafe(32)


def generate_pkce():
    verifier = generate_verifier()

    return {
        "code_verifier": verifier,
        "code_challenge": challenge_from_verifier(verifier),
        "state": generate_state(),
    }
