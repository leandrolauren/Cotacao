import os
from typing import List, Optional

import psycopg2 as pg
from dotenv import load_dotenv
from pydantic import BaseModel, Field


# Output model for a single historical record
class HistoryRecord(BaseModel):
    date: str = Field(..., title="Date", description="Date of the record")
    close: float = Field(..., description="Price of the closing of the stock")
    message: Optional[str] = Field(None, description="Message for the user")


# Model for output with history pagination
class PaginatedHistory(BaseModel):
    success: bool = Field(..., description="Indicates whether the query was successful")
    data: List[HistoryRecord] = Field(..., description="List of historical records")
    pagination: dict = Field(
        ..., description="Info for pagination (actual page, total pages, etc.)"
    )
    message: Optional[str] = Field(None, description="Message for the user")


# Model for input validation
class RequestHistoryParams(BaseModel):
    ticker: str = Field(
        ...,
        min_length=1,
        max_length=10,
        pattern="^[A-Z0-9.]+$",
        description="Symbol of the stock, e.g., 'AAPL'",
    )
    days: int = Field(
        ...,
        gt=0,
        le=1825,
        description="Number of days for consulting the history of the stock (between 1 and 1825)",
    )

    page: int = Field(
        gt=0, description="Number of the page for pagination (default: 1)"
    )


# Model for Calculate validation
class CalculationRequest(BaseModel):
    initial_value: float = Field(
        ..., ge=0.0, description="Initial value for calculate", title="Initial Value"
    )
    monthly_contribution: float = Field(
        ...,
        ge=0.0,
        description="Monthly contribution amount",
        title="Monthly Contribution",
    )
    annual_interest: float = Field(
        ..., gt=0.0, description="Annual interest rate.", title="Annual Interest"
    )
    months: int = Field(
        ..., gt=0, description="Number of months for calculation", title="Months"
    )


# Model for response calculated
class ResponseCalculation(BaseModel):
    success: bool = Field(..., description="Indicates whether the query was successful")
    data: dict = Field(..., description="Dictionary of values for each month.")
    message: Optional[str] = Field(None, description="Message for the user.")


load_dotenv()


class Connection(object):
    def __init__(self):
        self.conn = None
        self.cursor = None
        self._connect()

    def _connect(self):
        if self.conn is None or self.conn.closed:
            self.conn = pg.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
            )
            self.cursor = self.conn.cursor()
            self.conn.autocommit = False
        elif self.cursor is None or self.cursor.closed:
            self.cursor = self.conn.cursor()

    def _validate_query(self, query: str, params=None):
        if not isinstance(params, (tuple, list, type(None))):
            raise TypeError("params must be a tuple or list")

        allowed_queries = {"SELECT", "INSERT", "UPDATE", "DELETE"}
        query_type = query.strip().split()[0].upper()
        if query_type not in allowed_queries:
            raise ValueError("Invalid query type")

    def _execute_query(self, query: str, params=None):
        self._connect()
        self.cursor.execute(query, params or ())

        query_lower = query.strip().lower()
        if query_lower.startswith("select"):
            return self.cursor.fetchall()
        elif query_lower.startswith("insert") and "returning" in query_lower:
            return self.cursor.fetchone()
        return self.cursor.rowcount

    def execute(self, query: str, params=None):
        self._validate_query(query, params)
        try:
            return self._execute_query(query, params)
        except (pg.OperationalError, pg.InterfaceError):

            return self._execute_query(query, params)

    def get_email_user_by_id(self, user_id: int):
        """
        Fetch user email by user ID.
        Returns the email string if found, None if not found.
        Raises ValueError if user_id is invalid.
        """
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("Invalid user ID. It must be a positive integer.")

        select_user_query = "SELECT email FROM users WHERE id = %s"
        result = self.execute(select_user_query, (user_id,))

        if result and len(result) > 0:
            return result[0][0]
        return None

    def commit(self):
        self._connect()
        self.conn.commit()

    def rollback(self):
        self._connect()
        self.conn.rollback()

    def close(self):
        if self.cursor and not self.cursor.closed:
            self.cursor.close()
        if self.conn and not self.conn.closed:
            self.conn.close()
