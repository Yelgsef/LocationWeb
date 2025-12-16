from pathlib import Path
import os
from functools import lru_cache
from typing import Any, Dict

from dotenv import load_dotenv
import pyrebase


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")


def required_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Missing environment variable: {key}")
    return value


config = {
    "apiKey": required_env("FIREBASE_API_KEY"),
    "authDomain": required_env("FIREBASE_AUTH_DOMAIN"),
    "projectId": required_env("FIREBASE_PROJECT_ID"),
    "storageBucket": required_env("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": required_env("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": required_env("FIREBASE_APP_ID"),
}

database_url = os.getenv("FIREBASE_DATABASE_URL")
if database_url:
    config["databaseURL"] = database_url

measurement_id = os.getenv("FIREBASE_MEASUREMENT_ID")
if measurement_id:
    config["measurementId"] = measurement_id


@lru_cache(maxsize=1)
def get_firebase_app():
    """Create (and cache) the Pyrebase app instance."""
    return pyrebase.initialize_app(config)


@lru_cache(maxsize=1)
def get_auth():
    """Return cached Firebase Auth client."""
    return get_firebase_app().auth()


def sign_in_with_email_password(email: str, password: str) -> Dict[str, Any]:
    """
    Sign in with Firebase Authentication using email/password.
    Returns idToken/refreshToken and basic profile info.
    """
    email = (email or "").strip()
    password = password or ""
    if not email or not password:
        raise ValueError("Email và mật khẩu không được để trống.")

    try:
        auth = get_auth()
    except Exception as exc:  # pragma: no cover - runtime failures
        raise RuntimeError("Không thể khởi tạo Firebase Auth.") from exc

    try:
        session = auth.sign_in_with_email_and_password(email, password)
        account = auth.get_account_info(session["idToken"]) if session.get("idToken") else None
    except Exception as exc:
        raise ValueError("Sai email hoặc mật khẩu.") from exc

    expires_in = int(session.get("expiresIn", 0) or 0)
    user_info = (account or {}).get("users", [{}])[0]
    return {
        "email": user_info.get("email", email),
        "localId": session.get("localId"),
        "idToken": session.get("idToken"),
        "refreshToken": session.get("refreshToken"),
        "expiresIn": expires_in,
    }


# Backwards-compatible aliases
auth = get_auth()
firebase_app = get_firebase_app()
