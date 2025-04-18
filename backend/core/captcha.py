import os

import requests
from dotenv import load_dotenv

load_dotenv()


def verify_recaptcha(response_token: str) -> bool:
    """
    Verify the CAPTCHA token using Google's reCAPTCHA API.
    Expects RECAPTCHA_SECRET_KEY in the environment variables.
    """
    secret = os.getenv("RECAPTCHA_SECRET_KEY")
    if not secret:
        raise ValueError("Missing RECAPTCHA_SECRET_KEY in environment variables.")

    url = "https://www.google.com/recaptcha/api/siteverify"
    payload = {
        "secret": secret,
        "response": response_token,
    }
    response = requests.post(url, data=payload)
    result = response.json()
    return result.get("success", False)
