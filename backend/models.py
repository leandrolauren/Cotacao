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
        description="Symbol of the stock, e.g., 'AAPL'",
    )
    days: int = Field(
        ...,
        gt=0,
        le=365,
        description="Number of days for consulting the history of the stock (between 1 and 365)",
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

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super(Connection, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.__check_var()

        try:
            self.conn = pg.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
            )
            self.cursor = self.conn.cursor()

        except pg.Error as e:
            raise ConnectionError(f"Error connecting to the database: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            self.conn.rollback()

        else:
            self.conn.commit()

        if self.cursor:
            self.cursor.close()

        if self.conn:
            self.conn.close()

    def __check_var(self):
        required_vars = ["DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT"]

        for var in required_vars:
            if not os.getenv(var):
                raise ValueError(f"Environment variable {var} is not set.")

    def execute(self, query: str, params=None):
        self.cursor.execute(query, params or ())

        if query.strip().lower().startswith("select"):
            return self.cursor.fetchall()
        else:
            return self.cursor.rowcount

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()


class DownloadRequest(BaseModel):
    """
        Media download request scheme.

    Attributes:
        url (str): YouTube video URL.
        download_type (str): Download type ('video' or 'audio').
        download_path (str): Path to save the downloaded file.
        resolution (Optional[str]): Video resolution (default "maximum"). Applicable only for video downloads.
    """

    url: str = Field(..., example="https://www.youtube.com/watch?v=EXEMPLO")
    download_type: str = Field(
        ..., example="video", description="Download Type: 'video' or 'audio'."
    )
    download_path: str = Field(
        ..., example="videos_downloads", description="Path to save download."
    )
    resolution: Optional[str] = Field(
        "highest", example="highest", description="Video resolution, if applicable."
    )


if __name__ == "__main__":
    with Connection() as conn:
        result = conn.execute("select * from confirmations")
        print(hex(id(conn)))
        print(result)
