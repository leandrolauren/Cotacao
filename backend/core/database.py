import logging
import textwrap
from typing import Any, Dict

from fastapi import HTTPException, status

from backend.core.auth import Auth
from backend.models import Connection

logger = logging.getLogger(__name__)


class Database:
    """
    Database class to handle database-related tasks.
    This class is a singleton to ensure that only one instance is created.
    """

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.auth = None
        self._initialize_auth()

    def _initialize_auth(self):
        try:
            self.auth = Auth()
        except Exception as e:
            logger.error(f"Error initializing authentication: {e}")
            raise HTTPException(
                status_code=500, detail="Error initializing authentication."
            ) from e

    def create_table(self) -> Dict[str, Any]:
        """
        Create or verify the existence of the 'users' table in the database.
        This function ensures that the table has the necessary columns and constraints

        Returns:
            Dict: Result of the operation, indicating success or failure.
        """
        sql_query = textwrap.dedent(
            """\
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(512) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                
            );
            
            -- Create trigger to update the updated_at column on row update
            CREATE OR REPLACE FUNCTION update_modified_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            
            DROP TRIGGER IF EXISTS update_users_updated_at ON users;
            CREATE TRIGGER update_users_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW
            EXECUTE PROCEDURE update_modified_column();
        """
        )

        try:
            with Connection() as conn:
                conn.execute(sql_query)

            logger.info("Table created/verified successfully")
            return {
                "success": True,
                "message": "Table users created/verified with success",
            }

        except ValueError as ve:
            logger.error(f"Value error: {str(ve)}")
            raise HTTPException(
                status_code=500, detail="Internal server error during database setup"
            )
        except Exception as e:
            logger.exception("Critical error creating database table")
            raise HTTPException(
                status_code=500, detail="Internal server error during database setup"
            ) from e

    def get_user_from_db(self, email: str) -> dict:
        """
        This method queries the database to retrieve user information such as email,
        password hash, and active status. It logs the process and handles exceptions
        that may occur during the database operation.

        Args:
                - email (str): User email from login.
        Returns:
                - success (bool): Indicates whether the user was successfully found.
                - email (str, optional): The email of the user (if found).
                - password_hash (str, optional): The hashed password of the user (if found).
                - is_active (bool, optional): The active status of the user (if found).
                - message (str, optional): An error or informational message (if the user was not found).
            HTTPException: If an error occurs during the database query, an HTTP 500 exception
            is raised with a relevant error message.
        Logging:
                - The start of the user fetch operation.
                - Whether the user was found or not.
                - Any errors encountered during the database query.
                - Completion of the user fetch operation.

        """
        if not email:
            logger.error("Email is required to fetch user from database")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        sql_query = textwrap.dedent(
            """\
            SELECT 
                email, 
                password_hash, 
                is_active 
            FROM postgres.public.users 
            WHERE email= %s LIMIT 1;"""
        )

        try:
            logger.info(f"Fetching user with email: {email}")

            with Connection() as conn:
                result = conn.execute(
                    query=sql_query,
                    params=(email,),
                )
                if result:
                    data_user = result[0]
                    return {
                        "success": True,
                        "email": data_user[0],
                        "password_hash": data_user[1],
                        "is_active": data_user[2],
                    }
                else:
                    logger.info(f"No user found with email: {email}")
                    return {
                        "success": False,
                        "message": "User not found",
                    }

        except ValueError as ve:
            logger.error(f"Value error: {str(ve)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid input data, {str(ve)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except TypeError as te:
            logger.error(f"Type error: {str(te)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid input data, {str(te)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"Error fetching user from database: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error on consulting user in database",
                headers={"WWW-Authenticate": "Bearer"},
            )

        finally:
            logger.info("Finished fetching user from database")

    def user_register(self, email: str, password: str) -> dict:
        """
        Register a new user in the database.
        """
        if not email or not password:
            logger.error("Email and password are required for registration")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password are required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        hashed_password = self.auth.get_password_hash(password)

        sql_query = textwrap.dedent(
            """\
                INSERT INTO users (
                    email,
                    password_hash)
                VALUES 
                    (%s, %s) 
                RETURNING id
            """
        )
        try:
            with Connection() as conn:
                conn.execute(
                    query=sql_query,
                    params=(
                        email,
                        hashed_password,
                    ),
                )
                return {
                    "success": True,
                    "message": f"User registered successfully",
                }

        except ValueError as ve:
            logger.error(f"Value error: {str(ve)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid input data",
                headers={"WWW-Authenticate": "Bearer"},
            )

        except Exception as e:
            logger.error(f"Error registering user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )
