import datetime
import logging
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

load_dotenv()


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
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
        self.access_token_expires_minutes = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
        )
        self.secret_key = os.getenv("SECRET_KEY")
        self.algorithm = os.getenv("ALGORITHM", "HS256")

    def _check_settings(self):
        """
        Check if the required environment variables are set.
        Raises:
            ValueError: If any required environment variable is not set.
        """
        logger.info("Checking environment variables")
        required_vars = ["SECRET_KEY", "ALGORITHM", "ACCESS_TOKEN_EXPIRE_MINUTES"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
            raise ValueError(
                f"Missing environment variables: {', '.join(missing_vars)}"
            )

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against its hashed version.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Hash a plain password.
        """
        return self.pwd_context.hash(password)

    def create_access_token(self, data: dict) -> str:
        """
        Create a JWT access token.
        """
        to_encode = data.copy()
        expire = datetime.now(tz=ZoneInfo("UTC")) + timedelta(
            minutes=self.access_token_expires_minutes
        )
        to_encode.update({"exp": expire.timestamp()})
        logger.debug(f"Creating access token with data: {to_encode}")
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, access_token: str) -> dict:
        """
        Verify a JWT access token and return the payload.
        """
        try:
            payload = jwt.decode(
                access_token, self.secret_key, algorithms=[self.algorithm]
            )

            if datetime.now(tz=ZoneInfo("UTC")) >= datetime.fromtimestamp(
                payload["exp"], tz=ZoneInfo("UTC")
            ):
                logger.warning("Token has expired")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            if "sub" not in payload:
                logger.warning("Token does not contain 'sub'")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid access token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            logger.debug(f"Token verified successfully: {payload}")
            return payload
        except JWTError:
            logger.error("Token verification failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token",
                headers={"WWW-Authenticate": "Bearer"},
            )
