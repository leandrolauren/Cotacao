import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm

from backend.core.auth import Auth
from backend.core.rate_limit import limiter

auth = Auth()


logger = logging.getLogger(__name__)

auth_router = APIRouter(tags=["Authentication"])


@auth_router.post("/token")
@limiter.limit("5/minute")
def get_token(request: Request, token: str = Depends(auth.oauth2_scheme)):
    """
    Endpoint to verify the access token.
    """
    logger.info("Verifying access token.")
    try:
        payload = auth.verify_token(access_token=token)

        if not payload:
            logger.warning("Invalid access token.")
            raise HTTPException(
                status_code=401,
                detail="Invalid access token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.info("Access token verified successfully.")
        return {"success": True, "token": token, "user": payload["sub"]}
    except HTTPException as e:
        logger.error(f"HTTP Error during token verification: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error verifying token: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail="An error occurred while verifying the token."
        )


@auth_router.post("/refresh")
@limiter.limit("5/minute")
async def refresh_token(
    request: Request, form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Endpoint to refresh the access token using a refresh token.
    """
    logger.info("Refreshing access token.")
    try:
        refresh_token = request.password

        # Verify the refresh token
        payload = auth.verify_token(access_token=refresh_token)
        if not payload:
            logger.warning("Invalid refresh token.")
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_email = payload["sub"]
        access_token = auth.create_access_token(
            data={"sub": user_email}, encrypt_sensitive_data=True
        )
        logger.info(f"Access token refreshed successfully for user: {user_email}")

        return {"success": True, "access_token": access_token, "token_type": "bearer"}
    except HTTPException as e:
        logger.error(f"HTTP Error during token refresh: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail="An error occurred while refreshing the token."
        )


@auth_router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint for user login, returning an access token.
    """
    logger.info(f"User login attempt: {form_data.username}")

    try:
        from backend.core.database import Database

        db = Database()
        result = db.get_user_from_db(email=form_data.username)

        if not result.get("success"):
            logger.warning(f"User {form_data.username} not found or invalid data.")
            raise HTTPException(
                status_code=400,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not auth.verify_password(
            plain_password=form_data.password, hashed_password=result["password_hash"]
        ):
            logger.warning(f"Invalid login attempt for user: {form_data.username}")
            raise HTTPException(
                status_code=400,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = auth.create_access_token(
            data={
                "sub": result["email"],
                "email": result["email"],
                "password": result["password_hash"],
            },
            encrypt_sensitive_data=True,
        )

        logger.info(f"User {form_data.username} logged in successfully.")

        return {"success": True, "access_token": access_token, "token_type": "bearer"}

    except HTTPException as e:
        logger.error(f"HTTP Error during login: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during login: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="An error occurred during login.")


@auth_router.post("/register")
@limiter.limit("3/minute")
async def register(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint for user registration.

    """
    logger.info(f"User registration attempt: {form_data.username}")

    try:

        if not form_data.username or not form_data.password:
            logger.warning("Username and password are required.")
            raise HTTPException(
                status_code=400,
                detail="Username and password are required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        from backend.core.database import Database

        db = Database()
        user = db.get_user_from_db(email=form_data.username)

        if user.get("success"):
            logger.warning(f"User {form_data.username} already exists.")
            raise HTTPException(
                status_code=400,
                detail="User already exists",
                headers={"WWW-Authenticate": "Bearer"},
            )

        db.user_register(email=form_data.username, password=form_data.password)
        logger.info(f"User {form_data.username} registered successfully.")

        return {"success": True, "message": "User registered successfully."}
    except HTTPException as e:
        logger.error(f"HTTP Error during registration: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during registration: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail="An error occurred during registration."
        )
