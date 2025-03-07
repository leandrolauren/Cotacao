# Cotação - Stock Information Application

## Description
Cotacao is a stock information application that allows users to fetch real-time stock data and historical prices. Built with FastAPI for the backend and React with Vite for the frontend, this application provides a seamless experience for stock market enthusiasts.

## Installation

### Backend
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Frontend
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install the required dependencies:
   ```bash
   npm install
   ```

## Usage

### Running the Backend
To start the backend server, run:
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### Running the Frontend
To start the frontend application, run:
```bash
npm start
```
The frontend will be available at `http://localhost:3000`.

## API Endpoints

### Fetch Stock Information
- **Endpoint**: `/stock/{ticker}`
- **Method**: GET
- **Description**: Fetches stock information based on the ticker symbol.
- **Example Request**: 
  ```
  GET /stock/AAPL
  ```

### Fetch Historical Prices
- **Endpoint**: `/history`
- **Method**: GET
- **Description**: Retrieves historical stock prices with pagination.
- **Example Request**: 
  ```
  GET /history?ticker=AAPL&days=30&page=1
  ```

### Calculate Compound Interest
- **Endpoint**: /calculation
- **Method**: POST
- **Description**: Calculates compound interest results (total value, invested amount, interest, and monthly breakdown).

## Request Body (JSON):

```json
   {
   "initial_value": 1000,
   "monthly_contribution": 100,
   "annual_interest": 8,
   "months": 12
   }
```

## Example Request:

```bash
   curl -X POST http://localhost:8000/calculation \
   -H "Content-Type: application/json" \
   -d '{
      "initial_value": 1000,
      "monthly_contribution": 100,
      "annual_interest": 8,
      "months": 12
   }'
```

## Features
- Real-time stock data fetching.
- Historical price retrieval with pagination.
- User-friendly interface built with React.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any suggestions or improvements.

## License
This project is licensed under the MIT License.
