import yfinance as yf


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
        Fetch stock data from Yahoo Finance.
        """
        try:

            self.data = yf.Ticker(self.symbol)
            info = self.data.info
            if not info:
                raise ValueError(f"Could not fetch data for {self.symbol}")

            return {
                "success": True,
                "data": {
                    "Name": info.get("shortName"),
                    "P/E": info.get("trailingPE"),
                    "EBITDA": info.get("ebitda"),
                    "Gross Margin": float(info.get("grossMargins") * 100),
                    "Net Margin": float(info.get("profitMargins") * 100),
                    "Sector": info.get("sector"),
                    "Industry": info.get("industry"),
                    "Description": info.get("longBusinessSummary"),
                    "Actual Price": info.get("currentPrice"),
                },
                "message": "Stock info fetched successfully",
            }
        except Exception as e:
            raise ValueError(f"Error fetching data for {self.symbol}: {str(e)}")


if __name__ == "__main__":
    stock = Stock("AAPL")

    print(stock.fetch_data())
