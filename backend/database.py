from fastapi import HTTPException
from models import Connection
import logging

logger = logging.getLogger(__name__)


def create_table():
    try:
        
        with Connection() as conn:
            response = conn.execute(
                """
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
                """
            )
        return {"success": True, "message": f"Table created successfully, {response}"}
    
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        logger.error(f"PGSQL Return: {response}")
        raise