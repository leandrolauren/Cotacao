import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

export const useStockHistory = (ticker) => {
  const { data: historyData, isLoading: isLoadingHistory } = useQuery({
    queryKey: ['stockHistory', ticker],
    queryFn: async () => {
      let allData = [];
      let page = 1;
      let totalPages = 1;
      
      do {
        const response = await axios.get('http://localhost:8000/history', {
          params: {
            ticker: ticker,
            days: 200,
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
    staleTime: 1000 * 60 * 5 // 5 minutes
  });


  return { historyData, isLoadingHistory };
};
