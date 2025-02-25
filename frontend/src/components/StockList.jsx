import axios from 'axios';
import { useState, useEffect } from 'react';
import StockCard from './StockCard';
import './StockList.css';

const StockList = () => {
  const [searchTicker, setSearchTicker] = useState('');
  const [stocksList, setStocksList] = useState([]);
  const [searchError, setSearchError] = useState(false);
  const [searchEqual, setSearchEqual] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const fetchStockData = async (ticker) => {
    try {
      const response = await axios.get(`https://cotacao.onrender.com/stock/${ticker}`);

      if (!response.data.success) {
        setSearchError(true);
        return null;
      }

      return {
        ticker,
        data: {
          currentPrice: response.data.data['Actual Price'] || 0,
          industry: response.data.data['Industry'] || 'N/A',
          sector: response.data.data['Sector'] || 'N/A',
          grossMargin: response.data.data['Gross Margin'] || 0,
          netMargin: response.data.data['Net Margin'] || 0,
          priceEarning: response.data.data['P/E'] || 0,
          variation: response.data.data['Variation'] || 0
        }
      };
    } catch (error) {
      console.error(`Error fetching stock ${ticker}:`, error);
      setSearchError(true);
      return null;
    }
  };

  const handleSearch = async () => {
    if (!searchTicker) return setSearchError(false);
    if (stocksList.some(stock => stock.ticker === searchTicker)) return setSearchEqual(true);

    setIsLoading(true);
    setSearchError(false);

    const newStock = await fetchStockData(searchTicker);

    if (newStock){
      setStocksList(prev => [...prev, newStock]);
      setSearchTicker('');
    }

    setIsLoading(false);
  };

  useEffect(() => {
    if (stocksList.length === 0) return;

    const interval = setInterval(async () => {
      console.log('Updating data..');
      const updatedStocks = await Promise.all(
        stocksList.map(async (stock) => {
          const updatedStock = await fetchStockData(stock.ticker);
          return updatedStock || stock;
        })
      );

      setStocksList(prev => prev.map ((stock, index) =>
        updatedStocks[index] ? updatedStocks[index] : stock
    ));
    }, 300000);

    return () => clearInterval(interval);
  }, [stocksList]);


  return (
    <div className="stock-list">
      <div className="search-container">
        <div className="search-input-container">
          <input
            type="text"
            value={searchTicker}
            onChange={(e) => {
              setSearchTicker(e.target.value.toUpperCase());
              setSearchError(false);
              setSearchEqual(false);
            }}
            className={searchError ? 'error' : ''}
            placeholder="Enter the stock ticker (ex: AAPL)"
          />
          {searchError && <span className="error-message">Ticker not found!</span>}
          {searchEqual && <span className="error-message">Ticker already consulted!</span>}
        </div>
        <button onClick={handleSearch} disabled={isLoading}>
          {isLoading ? 'Loading...' : 'Search'}
        </button>
      </div>
      
      <div className="cards-grid">
        {stocksList.map(stock => (
          <StockCard key={stock.ticker} ticker={stock.ticker} data={stock.data} />
        ))}
      </div>
    </div>
  );
};

export default StockList;