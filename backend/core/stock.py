import yfinance as yf

from backend.models import HistoryRecord, PaginatedHistory


class Stock:

    def __new__(cls, *args, **kwargs):
        """
        Singleton pattern to ensure only one instance of Stock exists.
        """
        if not hasattr(cls, "_instance"):
            cls._instance = super(Stock, cls).__new__(cls)
        return cls._instance

    def __init__(self, symbol):
        self.symbol = symbol
        self.data = None

    def fetch_data(self):
        """
        Fetch stock data from Yahoo Finance using yfinance.
        Returns:
            dict: A dictionary containing stock information.
        Raises:
            ValueError: If the stock symbol is invalid or data cannot be fetched.
        """
        try:

            self.data = yf.Ticker(self.symbol)

            if not self.data.info:
                raise ValueError(f"Could not fetch data for {self.symbol}")

            return {
                "success": True,
                "data": {
                    "Name": self.data.info.get("shortName"),
                    "P/E": self.data.info.get("trailingPE"),
                    "EBITDA": self.data.info.get("ebitda"),
                    "Gross Margin": float(self.data.info.get("grossMargins") * 100),
                    "Net Margin": float(self.data.info.get("profitMargins") * 100),
                    "Sector": self.data.info.get("sector"),
                    "Industry": self.data.info.get("industry"),
                    "Description": self.data.info.get("longBusinessSummary"),
                    "Actual Price": self.data.info.get("currentPrice"),
                    "Previous Close": self.data.info.get("previousClose"),
                    "Regular Market Price": self.data.info.get("regularMarketPrice"),
                    "Market Cap": self.data.info.get("marketCap"),
                    "Dividend Rate": self.data.info.get("dividendRate"),
                    "Dividend Yield": self.data.info.get("dividendYield"),
                },
                "message": "Stock info fetched successfully",
            }
        except Exception as e:
            raise ValueError(f"Error fetching data for {self.symbol}: {str(e)}")

    def fetch_historical_data(
        self, days: int, page: int, page_size: int = 365
    ) -> PaginatedHistory:
        """
        Fetch historical stock data and paginate the results.
        Args:
            days (int): Number of days to fetch historical data for.
            page (int): Page number for pagination.
            page_size (int): Number of records per page.
        Returns:
            PaginatedHistory: Paginated historical stock data.
        """
        try:
            stock = yf.Ticker(self.symbol)
            history = stock.history(period=f"{days}d")

            if history.empty:
                raise ValueError(
                    "No historical data found for the specified ticker and time period."
                )

            # Pagination
            history.reset_index(inplace=True)
            history = history[["Date", "Close"]]
            start = (page - 1) * page_size
            end = start + page_size

            paginated_history = history.iloc[start:end]
            if paginated_history.empty:
                raise ValueError("No data available for the requested page.")

            records = [
                HistoryRecord(date=row["Date"].strftime("%Y-%m-%d"), close=row["Close"])
                for _, row in paginated_history.iterrows()
            ]

            return PaginatedHistory(
                success=True,
                pagination={
                    "current_page": page,
                    "page_size": page_size,
                    "total_pages": (len(history) + page_size - 1) // page_size,
                    "total_records": len(history),
                },
                data=records,
                message="Historical data fetched successfully.",
            )
        except Exception as e:
            raise ValueError(f"Error fetching historical data: {str(e)}")
