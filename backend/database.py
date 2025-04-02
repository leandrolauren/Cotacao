import logging
import textwrap
from typing import Any, Dict

from fastapi import HTTPException, status

from backend.models import Connection

logger = logging.getLogger(__name__)


def create_table() -> Dict[str, Any]:
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
            
            -- Indice for email column to speed up queries
            CONSTRAINT idx_users_email UNIQUE (email)
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
        return {"success": True, "message": "Table users created/verified with success"}

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


def get_user_from_db(email: str) -> dict:
    """
    Fetch user details from the database.
    """
    try:
        logger.info(f"Fetching user with email: {email}")
        with Connection() as conn:
            result = conn.execute(
                "SELECT email, password_hash, is_active FROM postgres.public.users WHERE email = %s",
                (email,),
            )
            data_user = result[0]
            if data_user:
                logger.info(f"User found: {data_user[0]}")
                return {
                    "email": data_user[0],
                    "password_hash": data_user[1],
                    "is_active": data_user[2],
                }
            else:
                logger.info(f"No user found with email: {email}")
                return None
    except Exception as e:
        logger.error(f"Error fetching user from database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error on consulting user in database",
            headers={"WWW-Authenticate": "Bearer"},
        )

    finally:
        logger.info("Finished fetching user from database")
