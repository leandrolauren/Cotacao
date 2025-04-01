import datetime
from zoneinfo import ZoneInfo
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta

sp_timezone = ZoneInfo("America/Sao_Paulo")

logger = logging.getLogger(__name__)

load_dotenv()


class Auth:
    """
    Auth class to handle authentication-related tasks.
    This class is a singleton to ensure that only one instance is created.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
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
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15)
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
        expire = datetime.now(sp_timezone) + timedelta(
            minutes=self.access_token_expires_minutes
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)


if __name__ == "__main__":
    auth1 = Auth()
    print("Token", auth1.create_access_token({"sub": "test_user"}))
    print("Hash Password", auth1.get_password_hash("test_password"))
    print("Hash Password", auth1.get_password_hash("1234"))
