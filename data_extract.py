import requests
import pandas as pd
from datetime import datetime, timedelta
import time

class FetchData:
    """
    A class responsible for fetching historical market data from the Polygon.io API.

    Attributes:
        api_key (str): API key for authenticating requests to the Polygon.io API.
    """
    
    def __init__(self, api_key):
        self.api_key = api_key

    def fetch_data(self, ticker, timespan, multiplier=1):
        """
        Fetch historical data for a ticker with specified timespan and multiplier.
        """
        if timespan in ['minute', 'hour']:
            # For timeframes of an hour or less, query in 3 chunks if multiplier allows
            df = self._fetch_data_in_chunks(ticker, timespan, multiplier)
        else:
            # For other cases, fetch data normally
            df = self._fetch_single_chunk(ticker, timespan, multiplier)

        return df

    def _fetch_data_in_chunks(self, ticker, timespan, multiplier):
        """
        Fetches data in chunks and combines them into a single DataFrame.
        """
        chunks = 3  # Number of chunks to split the query into (Around 3 months should be plenty for lower time frames)
        dfs = []
        end_date = datetime.now() 
        for i in range(chunks):
            start_date = end_date - timedelta(minutes=(50000))
            dfs.append(self._fetch_single_chunk(ticker, timespan, multiplier, start_date, end_date))
            # Update end time
            end_date = end_date - timedelta(minutes=(50001))
        
        combined_df = pd.concat(dfs).drop_duplicates().sort_index()

        # Avoid getting rate limited!!!
        time.sleep(0.5)

        return combined_df

    def _fetch_single_chunk(self, ticker, timespan, multiplier, start_date=None, end_date=None):
        """
        Fetches a single chunk of data based on the provided start and end dates.
        """
        if not start_date:
            start_date = self._calculate_start_date(timespan)
        if not end_date:
            end_date = datetime.now()
            
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{start_date_str}/{end_date_str}"
        params = {'apiKey': self.api_key, 'multiplier':multiplier, 'timespan':timespan, 'limit': 50000}

        print(f'Fetching {multiplier} {timespan} data for ticker {ticker}: {start_date} - {end_date}')
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json().get('results', [])
            if data:
                df = pd.DataFrame(data)
                df.rename(columns={'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 'v': 'volume', 't': 'timestamp'}, inplace=True)
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                return df
        else:
            print(f"API request failed with status code {response.status_code}: {response.text}")
        return pd.DataFrame()

    def _calculate_start_date(self, timespan):
        """
        Calculates the start date for the API request based on the maximum number of entries allowed.
        """
        if timespan == 'minute':
            return datetime.now() - timedelta(minutes=50000) 
        elif timespan == 'hour':
            return datetime.now() - timedelta(hours=50000)  
        elif timespan == 'day':
            return datetime.now() - timedelta(days=1825)  # Start date 5 years ago
        elif timespan == 'week':
            return datetime.now() - timedelta(days=1825)  # Start date 5 years ago
        elif timespan == 'month':
            return datetime.now() - timedelta(days=1825)  # Start date 5 years ago
        elif timespan == 'quarter':
            return datetime.now() - timedelta(days=1825)  # Start date 5 years ago
        elif timespan == 'year':
            return datetime.now() - timedelta(days=1825)  # Start date 5 years ago
        else:
            raise ValueError(f"Unsupported timespan: {timespan}")