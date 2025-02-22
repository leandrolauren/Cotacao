import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import StockCard from './StockCard';
import './StockList.css';

const StockList = () => {
  const [searchTicker, setSearchTicker] = useState('');
  const [stocksList, setStocksList] = useState([]);
  const [searchError, setSearchError] = useState(false);

  const { isLoading, isError } = useQuery({
    queryKey: ['stocks'],
    queryFn: async () => {
      const response = await axios.get('http://localhost:8000/stock/AAPL');
      setStocksList(prev => [{
        ticker: 'AAPL',
        data: {
          currentPrice: response.data.data['Actual Price'],
          industry: response.data.data['Industry'],
          sector: response.data.data['Sector'],
          grossMargin: response.data.data['Gross Margin'],
          netMargin: response.data.data['Net Margin'],
          priceEarning: response.data.data['P/E'],
          variation: response.data.data['Variation']
        }
      }, ...prev]);
      return [];
    },
    refetchOnWindowFocus: false
  });

  const handleSearch = async () => {
    try {
      const response = await axios.get(`http://localhost:8000/stock/${searchTicker}`);
      
      if (!response.data.sucess) {
        setSearchError(true);
        return;
      }

      const newStock = {
        ticker: searchTicker,
        data: {
          currentPrice: response.data.data['Actual Price'],
          industry: response.data.data['Industry'],
          sector: response.data.data['Sector'],
          grossMargin: response.data.data['Gross Margin'],
          netMargin: response.data.data['Net Margin'],
          priceEarning: response.data.data['P/E'],
          variation: response.data.data['Variation']
        }
      };
      
      setStocksList(prev => [...prev, newStock]);
      setSearchTicker('');
      setSearchError(false);
    } catch (error) {
      console.error('Error fetching stock:', error);
      setSearchError(true);
    }
  };

  if (isLoading) return <div>Carregando ações...</div>;
  if (isError) return <div>Erro ao carregar ações</div>;

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
            }}
            className={searchError ? 'error' : ''}
            placeholder="Digite o ticker da ação (ex: AAPL)"
          />
          {searchError && <span className="error-message">Ticker não encontrado!</span>}
        </div>
        <button onClick={handleSearch}>Buscar</button>
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
