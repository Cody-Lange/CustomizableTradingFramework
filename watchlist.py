import requests
import vectorbt as bt

class WatchlistItem:
    """
    Represents an item in the watchlist, holding details about the asset, its current price,
    associated trading framework, and the results of evaluations and backtests.

    Attributes:
        name (str): Human-readable name of the asset.
        ticker (str): Ticker symbol of the asset.
        asset_type (str): Type of the asset (e.g., 'Stock', 'Crypto').
        api_key (str): API key used for fetching data.
        current_price (float): Current price of the asset. Default is None.
        framework (TradingFramework): Trading framework associated with this asset. Default is None.
        framework_results (dict): Results from the latest framework evaluation. Default is None.
        backtest_results (object): Results object from the last backtest. Default is None.
        backtest_pnl_percent (float): Percentage P&L from the last backtest. Default is None.
    """
    def __init__(self, name, ticker, asset_type, api_key, current_price=None, framework=None):
        """Initializes a new Watchlist instance with the provided API key."""
        self.name = name
        self.ticker = ticker
        self.asset_type = asset_type
        self.api_key = api_key
        self.current_price = current_price
        self.framework = framework
        self.framework_results = {"timeframe_statuses": None, "overall_status": None}
        self.backtest_results = None
        self.backtest_pnl_percent = None

    def fetch_current_price(self):
        """
        Fetches and updates the current price of the asset using the API.
        Handles both stock and crypto assets based on the asset_type.
        """
        url = ''
        if self.asset_type == 'Stock':
            url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/{self.ticker}?apiKey={self.api_key}"
        elif self.asset_type == 'Crypto':
            url = f"https://api.polygon.io/v2/snapshot/locale/global/markets/crypto/tickers/{self.ticker}?apiKey={self.api_key}"
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if self.asset_type == 'Stock':
                self.current_price = data['ticker']['min']['o']
            elif self.asset_type == 'Crypto':
                self.current_price = data['ticker']['min']['o']
        else:
            print(f"Failed to fetch current price for {self.ticker}: {response.text}")

    def evaluate_framework(self):
        """
        Evaluates the associated trading framework against the asset. Updates
        the framework_results with timeframe statuses and overall status.
        """
        if self.framework:
            print(f"Evaluating framework for {self.ticker}")
            timeframe_statuses = self.framework.evaluate_all_timeframes()
            overall_status = self.framework.determine_overall_status(self.framework.bias_timeframes, self.framework.confirmation_timeframes)
            self.framework_results = {"timeframe_statuses": timeframe_statuses, "overall_status": overall_status}
            print("Timeframe Statuses:", timeframe_statuses)
            print("Overall Trading Status:", overall_status)
        else:
            print(f"No framework assigned to {self.ticker}.")

    def perform_backtest(self, initial_capital=10000):
        """
        Performs backtesting on the asset using the associated framework and historical data.
        Stores the backtest results and calculates P&L percentage.

        Args:
            initial_capital (float): The starting capital for the backtest. Default is 10,000.
        """
        if self.framework:
            print(f"Performing backtest for {self.ticker}")
            self.backtest_results = self.framework.backtest(initial_capital=initial_capital)
            self.backtest_pnl_percent = round(self.backtest_results.total_return() * 100, 2)
            print(f"Backtest completed for {self.ticker}")
        else:
            print(f"No framework assigned for backtesting {self.ticker}.")
            self.backtest_results = None

    def __str__(self):
        return f"{self.name} ({self.ticker}) - {self.asset_type}: Current Price: {self.current_price}, Framework Overall Status: {self.framework_results['overall_status']}, Backtest P&L%: {self.backtest_pnl_percent}"

class Watchlist:
    """
    Manages a collection of WatchlistItems, allowing for operations like adding and removing items,
    updating prices, evaluating trading frameworks, and performing backtests.

    Attributes:
        api_key (str): API key used for data fetching across all watchlist items.
        items (dict): Dictionary holding WatchlistItems, keyed by their ticker symbols.
    """
    def __init__(self, api_key):
        self.api_key = api_key
        self.items = {}  

    def add_item(self, name, ticker, asset_type, framework=None):
        """
        Adds a new item to the watchlist.

        Args:
            name (str): Name of the asset.
            ticker (str): Ticker symbol of the asset.
            asset_type (str): Type of the asset (e.g., 'Stock', 'Crypto').
            framework (TradingFramework): Optional. Trading framework to associate with this asset.
        """
        print(f'Adding {ticker} to watchlist')
        self.items[ticker] = WatchlistItem(name, ticker, asset_type, self.api_key, framework=framework)

    def remove_item(self, ticker):
        """
        Removes an item from the watchlist by its ticker symbol.

        Args:
            ticker (str): Ticker symbol of the item to remove.
        """
        if ticker in self.items:
            print(f'Removing {ticker} from watchlist')
            del self.items[ticker]

    def update_prices(self):
        """Updates the current prices for all items in the watchlist."""
        for ticker, item in self.items.items():
            print(f'Updating price for {ticker}')
            item.fetch_current_price()

    def evaluate_frameworks(self):
        """Evaluates the trading frameworks for all items in the watchlist."""
        print("Evaluating frameworks for all watchlist items...")
        for item in self.items.values():
            item.evaluate_framework()

    def perform_backtests(self, initial_capital=10000):
        """
        Initiates backtesting for all items in the watchlist using their associated frameworks.

        Args:
            initial_capital (float): The starting capital for the backtests. Default is 10,000.
        """
        print("Performing backtests for all watchlist items...")
        for item in self.items.values():
            item.perform_backtest(initial_capital=initial_capital)

    def show(self):
        for item in self.items.values():
            print(item)