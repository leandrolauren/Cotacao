import { useState } from 'react';
import { useStockHistory } from '../hooks/useStockHistory';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);


const StockCard = ({ ticker, data = {} }) => {
  const [ showHistory, setShowHistory] = useState(false);
  const { historyData } = useStockHistory(ticker);
  
  const chartData = {
    labels: historyData?.map(item => item.date) || [],
    datasets: [
        {
          label: 'Close Price',
          data: historyData?.map(item => item.close) || [],
          borderColor: 'rgb(88, 207, 187)',
          tension: 0.01,
          pointRadius: 0,
          pointHoverRadius: 5
        }

    ]
  };

  
  const { 
    currentPrice = 0, 
    industry = '', 
    sector = '', 
    grossMargin = 0,
    netMargin = 0,
    priceEarning = 0,
    variation = 0
  } = data;

  const grossMarginClass = grossMargin >= 0 ? 'positive' : 'negative';
  const grossMarginSign = grossMargin >= 0 ? '+' : '';

  const netMarginClass = netMargin >= 0 ? 'positive' : 'negative';
  const netMarginSign = netMargin >= 0 ? '+' : '';

  const variationClass = variation >= 0 ? 'positive' : 'negative';
  const variationSign = variation >= 0 ? '+' : '';
  
  return (
    <div className="stock-card">
      <div className="card-actions">
        <button 
          className="history-button"
          onClick={() => setShowHistory(true)}
        >
          History
        </button>
      </div>

      <div className="stock-header">
        <h3>{ticker || 'N/A'}</h3>
        <span className="price">${currentPrice?.toFixed(2) || '0.00'}</span>
      </div>
      <div className="stock-info">

        <div className="info-item">
          <span>Industry</span>
          <span>{industry}</span>
        </div>

        <div className="info-item">
          <span>Sector</span>
          <span>{sector}</span>
        </div>

        <div className="info-item">
          <span>Gross Margin</span>
          <span className={grossMarginClass}>
            {grossMarginSign}{grossMargin?.toFixed(2) || '0.00'}%
          </span>
        </div>

        <div className="info-item">
          <span>Net Margin</span>
          <span className={netMarginClass}>
            {netMarginSign}{netMargin?.toFixed(2) || '0.00'}%
          </span>
        </div>
        
        <div className="info-item">
          <span>P/E</span>
          <span>{priceEarning?.toFixed(2)}</span>
        </div>

        <div className="info-item">
          <span>Variation</span>
          <span className={variationClass}>
            {variationSign}{variation?.toFixed(2)}%
          </span>
        </div>

      </div>

      {showHistory && (
        <div className="chart-container">
          <Line 
            data={chartData}
            options={{
              responsive: true,
              scales: {
                x: {
                  display: false
                }
              },
              interaction: {
                intersect: false,
                mode: 'index'
              },

              plugins: {
                legend: {
                  position: 'top',
                  display: false,
                },
                title: {
                  display: true,
                  text: `Price History - ${ticker}`,
                },
              },
            }}

          />
        </div>
      )}

    </div>
  );
};

export default StockCard;
