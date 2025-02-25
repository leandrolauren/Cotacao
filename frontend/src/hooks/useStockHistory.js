import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

export const useStockHistory = (ticker) => {
  const { data: historyData, isLoading: isLoadingHistory } = useQuery({
    queryKey: ['stockHistory', ticker],
    queryFn: async () => {
      if (!ticker) return null;

      let allData = [];
      let page = 1;
      let totalPages = 1;
      
      do {
        const response = await axios.get('https://cotacao.onrender.com/history', {
          params: {
            ticker: ticker,
            days: 365,
            page: page
          }
        });
        
        allData = [...allData, ...response.data.data];
        totalPages = response.data.pagination.total_pages;
        page++;
      } while (page <= totalPages);

      return allData;
    },
    enabled: !!ticker,
    refetchInterval: 8 * 60 * 60 * 1000,
    staleTime: 8 * 60 * 60 * 1000
  });


  return { historyData, isLoadingHistory };
};
