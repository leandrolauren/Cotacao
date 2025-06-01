# Cotação - Stock Information Application

## Description

Cotação is a stock information application that allows users to fetch real-time stock data, historical prices and perform financial calculations. The backend is built using FastAPI and employs JWT-based authentication with sensitive data encryption via Fernet.

**Features:**

- Real-time stock data fetching using Yahoo Finance (via yfinance)
- Historical stock price retrieval with pagination
- Financial calculations (compound interest and monthly breakdown)
- User authentication and registration (login, token verification, token refresh)
- Environment variable-based configuration for database and JWT secrets.

## Installation

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Cotacao
   ```
2. **Create and activate a virtual environment:**
   - **Windows:**
     ```cmd
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - **Linux/Mac:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
3. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Environment Variables

Ensure you have a `.env` file in the project root with the following variables:

```properties
# Database connection details
DB_NAME="postgres"
DB_USER="<db_user>"
DB_PASSWORD="<password>"
DB_HOST="<host>"
DB_PORT="5432"

# JWT Token configuration
SECRET_KEY="<secret_key>  # Must be 32 url-safe Base64-encoded bytes (update if needed)
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=500

# Environment configuration
ENVIRONMENT="development"

```

> **Note:** The `SECRET_KEY` must be a valid 32-byte url-safe Base64-encoded string. You can generate one using:
>
> ```python
> from cryptography.fernet import Fernet
> print(Fernet.generate_key().decode())
> ```

## Running the Application

### Using Uvicorn

To start the backend server in development mode with auto-reload, run:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### Using Docker

Build and run using Docker:

1. **Build the image:**
   ```bash
   docker build -t cotacao-app .
   ```
2. **Run the container:**
   ```bash
   docker run -p 8000:8000 cotacao-app
   ```

## API Endpoints

### Authentication Endpoints

- **User Login**  
  **Endpoint:** `/login`  
  **Method:** POST  
  **Description:** Accepts username (email) and password via an OAuth2PasswordRequestForm, verifies credentials, and returns a JWT access token with sensitive fields (email, password hash) encrypted.

  **Example Request (cURL):**

  ```bash
  curl -X POST http://localhost:8000/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=user@example.com&password=yourpassword"
  ```

- **Token Verification**  
  **Endpoint:** `/token`  
  **Method:** POST  
  **Description:** Verifies the provided access token and returns the token along with the user subject if valid.
- **Refresh Token**  
  **Endpoint:** `/refresh`  
  **Method:** POST  
  **Description:** Accepts a refresh token (provided as a password in form data), verifies it, and returns a new access token.
- **User Registration**  
  **Endpoint:** `/register`  
  **Method:** POST  
  **Description:** Registers a new user with the provided email and password.

### Stock Endpoints

- **Fetch Stock Information**  
  **Endpoint:** `/stock/{ticker}`  
  **Method:** GET  
  **Description:** Retrieves real-time stock information for the given ticker symbol.  
  **Example Request:**
  ```
  GET /stock/AAPL
  ```
- **Fetch Historical Stock Prices**  
  **Endpoint:** `/history`  
  **Method:** GET  
  **Description:** Retrieves historical stock prices with pagination.  
  **Required Query Parameters:**
  - `ticker` (string): Stock ticker symbol
  - `days` (integer): Number of days of history (1 to 365)
  - `page` (integer): Page number for pagination  
    **Example Request:**
  ```
  GET /history?ticker=AAPL&days=30&page=1
  ```

### Calculation Endpoint

- **Calculate Compound Interest**  
  **Endpoint:** `/calculation`  
  **Method:** POST  
  **Description:** Performs a financial calculation based on initial value, monthly contribution, annual interest rate, and number of months. Returns the total value, invested amount, total interest, and monthly breakdown.

  **Request Body (JSON):**

  ```json
  {
    "initial_value": 1000,
    "monthly_contribution": 100,
    "annual_interest": 8,
    "months": 12
  }
  ```

  **Example Request (cURL):**

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

## Database Setup

The application uses PostgreSQL as its database. Connection details are configured via the following environment variables in your `.env`:

- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`

The **Database** class in the project creates a `users` table (if not existing) with columns for email, password hash, and status. It also includes a trigger to update the `updated_at` column on record modifications.

## Additional Information

- **Logging:**  
  The logging configuration is set up in `main.py` to log detailed information including timestamps, log levels, origins, and messages.
- **Security Considerations:**
  - JWT tokens are signed using the provided `SECRET_KEY` and the HS256 algorithm.
  - Sensitive data (such as email and password hash) included in the JWT payload are encrypted using Fernet symmetric encryption.
  - All environment configurations are loaded from the `.env` file using `python-dotenv`.
- **Modifications:**  
  This README now includes details for endpoints related to authentication (login, token verification, refresh, and registration), stock information retrieval, historical data pagination and financial calculations. It also details environment variable configuration, database connection, and special logging/middleware setups.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License.
