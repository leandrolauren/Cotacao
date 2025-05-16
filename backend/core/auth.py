import datetime
import logging
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv
from fastapi import HTTPException, status
from fastapi.security import APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

load_dotenv(override=True)


class Auth:
    """
    Auth class to handle authentication-related tasks.
    This class is a singleton to ensure that only one instance is created.
    """

    def __new__(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = super(Auth, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._setup()

    def _setup(self):

        self._check_settings()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.oauth2_scheme = APIKeyHeader(name="Authorization", auto_error=False)
        self.access_token_expires_minutes = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
        )
        self.secret_key = os.getenv("SECRET_KEY")
        self.algorithm = os.getenv("ALGORITHM", "HS256")

        # Validate SECRET_KEY
        if len(self.secret_key) < 32:
            logger.error("SECRET_KEY must be at least 32 characters long.")
            raise ValueError("SECRET_KEY must be at least 32 characters long.")
        if not any(char.isalnum() for char in self.secret_key):
            logger.error("SECRET_KEY must contain alphanumeric characters.")
            raise ValueError("SECRET_KEY must contain alphanumeric characters.")

    def _check_settings(self):
        """
        Check if the required environment variables are set and validate the SECRET_KEY.
        Raises:
            ValueError: If any required environment variable is not set or invalid.
        """
        logger.info("Checking environment variables")
        required_vars = ["SECRET_KEY", "ALGORITHM", "ACCESS_TOKEN_EXPIRE_MINUTES"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
            raise ValueError(
                f"Missing environment variables: {', '.join(missing_vars)}"
            )

    def _encrypt_data(self, data: str) -> str:
        """
        Encrypt sensitive data using Fernet symmetric encryption.
        Args:
            data (str): The data to encrypt.
        Returns:
            str: The encrypted data (Base64-encoded).
        """
        if not self.secret_key:
            raise ValueError("SECRET_KEY is not set. Cannot encrypt data.")

        f = Fernet(self.secret_key)

        encrypted_data = f.encrypt(data=data.encode())

        return encrypted_data.decode()

    def _decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data using Fernet symmetric encryption.
        Args:
            encrypted_data (str): The encrypted data to decrypt.
        Returns:
            str: The decrypted data.
        """
        if not self.secret_key:
            raise ValueError("SECRET_KEY is not set. Cannot decrypt data.")

        f = Fernet(key=self.secret_key)

        try:
            decrypted_data = f.decrypt(token=encrypted_data).decode()
            return decrypted_data

        except InvalidToken:
            logger.error("Invalid token. Decryption failed.")
            raise ValueError("Invalid encrypted data or secret key.")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against its hashed version.
        """
        return self.pwd_context.verify(secret=plain_password, hash=hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Hash a plain password.
        """
        return self.pwd_context.hash(secret=password)

    def create_access_token(
        self, data: dict, encrypt_sensitive_data: bool = False
    ) -> str:
        """
        Create a JWT access token.
        Args:
            data (dict): The payload to include in the token.
            encrypt_sensitive_data (bool): Whether to encrypt sensitive data in the payload.
        Returns:
            str: The generated JWT token.
        """
        to_encode = data.copy()

        if encrypt_sensitive_data:
            for key, value in to_encode.items():
                if key in ["email", "password", "password_hash"]:
                    to_encode[key] = self._encrypt_data(value)

        expire = datetime.now(tz=ZoneInfo("UTC")) + timedelta(
            minutes=self.access_token_expires_minutes
        )
        to_encode.update({"exp": expire.timestamp()})
        logger.debug(f"Creating access token with data: {to_encode}")

        return jwt.encode(
            claims=to_encode, key=self.secret_key, algorithm=self.algorithm
        )

    def verify_token(self, access_token: str) -> dict:
        """
        Verify a JWT access token and return the payload.
        Args:
            access_token (str): The JWT token to verify.
        Returns:
            dict: The decoded payload if the token is valid.
        """
        if access_token.lower().startswith("bearer "):
            access_token = access_token.split(" ")[1]

        try:
            payload = jwt.decode(
                access_token, self.secret_key, algorithms=[self.algorithm]
            )

            # Check expiration
            if datetime.now(tz=ZoneInfo("UTC")) >= datetime.fromtimestamp(
                payload["exp"], tz=ZoneInfo("UTC")
            ):
                logger.error("Token has expired")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            if "email" in payload:
                email = self._decrypt_data(encrypted_data=payload["email"])

            if "password" in payload:
                password_token = self._decrypt_data(encrypted_data=payload["password"])

            if not email or not password_token:
                logger.error("Token does not contain email or password")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            from backend.core.database import Database

            db_instance = Database()
            user_db = db_instance.get_user_from_db(email)

            if not user_db or password_token != user_db.get("password_hash"):
                logger.error("Invalid username or password in token")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            logger.info("Token verified successfully and user authenticated.")
            return payload

        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTClaimsError:
            logger.error("Invalid token claims")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError:
            logger.error("Token verification failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token",
                headers={"WWW-Authenticate": "Bearer"},
            )
