import pandas as pd
import pandas_ta as ta
from datetime import datetime
import vectorbt as vbt


class TradingFramework:
    """
    A comprehensive trading framework for evaluating and backtesting trading strategies
    across multiple timeframes and signal groups.

    Attributes:
        name (str): Name of the trading framework.
        timeframes (dict): A dictionary of timeframes, each associated with its data and signal groups.
        active_time_frame (str): The active timeframe that is currently being used for analysis.
        bias_timeframes (list): List of timeframes considered for establishing market bias.
        confirmation_timeframes (list): List of timeframes used for trade confirmation.
        strategies (dict): Stores trading strategies for each timeframe.
        last_update (dict): Timestamps of the last data update for each timeframe.
        last_calculation (dict): Timestamps of the last calculation or analysis performed for each timeframe.
    """
    def __init__(self, name, timeframes={}, active_time_frame=None, bias_timeframes=[], confirmation_timeframes=[]):
        self.name = name
        self.timeframes = timeframes  
        self.active_time_frame = active_time_frame
        self.bias_timeframes = bias_timeframes
        self.confirmation_timeframes = confirmation_timeframes
        self.strategies = {}
        self.last_update = {tf: datetime.min for tf in timeframes}
        self.last_calculation = {tf: datetime.min for tf in timeframes}

    def current_timestamp(self):
        # Placeholder implementation - might need to adjust later for timezone reasons?
        return datetime.now()

    def add_timeframe(self, name, data, strategy=None):
        if name in self.timeframes:
            self.timeframes[name]['data'] = data
            current_strategy = strategy if strategy else self.strategies.get(name, None)
            if current_strategy:
                data.ta.strategy(current_strategy)
                self.strategies[name] = current_strategy
            else:
                print(f"No strategy defined for updating timeframe {name}.")
        else:
            if strategy:
                data.ta.strategy(strategy)
            self.timeframes[name] = {'data': data, 'signal_groups': []}
            self.strategies[name] = strategy if strategy else ta.Strategy(name=f"{name} Default Strategy", description="Default strategy for new timeframe")
        
        self.last_update[name] = self.current_timestamp()

    def needs_update(self, name):
        last_calculated = self.last_calculation.get(name, datetime.min)
        last_updated = self.last_update.get(name, datetime.min)
        return last_updated > last_calculated

    def update_strategy(self, name, indicators):
        """Updates or defines a strategy for a given timeframe."""
        if name in self.timeframes:
            strategy = ta.Strategy(name=f"{name} Custom Strategy", ta=indicators)
            self.strategies[name] = strategy
        else:
            print(f"Timeframe {name} does not exist. Please add it first.")

    def apply_strategy(self, name):
        """Applies the strategy to the data of a specific timeframe."""
        if name in self.timeframes and name in self.strategies:
            data = self.timeframes[name]['data']
            strategy = self.strategies[name]
            data.ta.strategy(strategy)
            self.timeframes[name]['data'] = data  
        else:
            print(f"Strategy or timeframe {name} does not exist.")

    def delete_timeframe(self, name):
        """Deletes a timeframe."""
        if name in self.timeframes:
            del self.timeframes[name]
        else:
            print(f"Timeframe {name} does not exist.")

    def add_signal_group_to_timeframe(self, timeframe_name, signal_group):
        """Adds a signal group to an existing timeframe."""
        if timeframe_name in self.timeframes:
            self.timeframes[timeframe_name]['signal_groups'].append(signal_group)
        else:
            print(f"Timeframe {timeframe_name} does not exist.")

    def remove_signal_group_from_timeframe(self, timeframe_name, signal_group_name):
        """Removes a signal group from an existing timeframe."""
        if timeframe_name in self.timeframes:
            signal_groups = self.timeframes[timeframe_name]['signal_groups']
            self.timeframes[timeframe_name]['signal_groups'] = [sg for sg in signal_groups if sg.name != signal_group_name]
        else:
            print(f"Timeframe {timeframe_name} does not exist.")

    def set_active_time_frame(self, timeframe_name):
        """Sets the active timeframe for the trading strategy."""
        if timeframe_name in self.timeframes:
            self.active_time_frame = timeframe_name
        else:
            print(f"Timeframe {timeframe_name} does not exist.")

    def evaluate_timeframe(self, name):
        if name not in self.timeframes:
            print(f"Timeframe {name} does not exist.")
            return {}

        if self.needs_update(name):
            self.apply_strategy(name)
            self.last_calculation[name] = self.current_timestamp()

        timeframe = self.timeframes[name]
        timeframe_results = {}
        status_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
        
        for group in timeframe['signal_groups']:
            group_results = group.evaluate_group(timeframe['data'], self.last_calculation[name])
            
            timeframe_results[group.name] = group_results

            group_overall_status = group_results['Overall']
            status_counts[group_overall_status] += 1

        majority_status = max(status_counts, key=status_counts.get)
        if status_counts[majority_status] == len(status_counts) / 2:  # Handling tie
            majority_status = 'neutral'

        timeframe_results['Overall'] = majority_status

        return timeframe_results

    def evaluate_all_timeframes(self):
        """Evaluates each timeframe and returns their statuses including individual signal scores."""
        all_timeframe_statuses = {}
        
        for name in self.timeframes.keys():
            all_timeframe_statuses[name] = self.evaluate_timeframe(name)
            
        return all_timeframe_statuses

    def determine_overall_status(self, bias_timeframes, confirmation_timeframes):
        status_count = {'positive': 0, 'neutral': 0, 'negative': 0}

        for tf in bias_timeframes:
            if tf in self.timeframes:
                tf_status = self.evaluate_timeframe(tf)['Overall']
                if tf_status in status_count:
                    status_count[tf_status] += 1


        for tf in confirmation_timeframes:
            if tf in self.timeframes:
                tf_status = self.evaluate_timeframe(tf)['Overall']
                if tf_status in status_count:
                    status_count[tf_status] += 1

        if self.active_time_frame and self.active_time_frame in self.timeframes:
            tf_status = self.evaluate_timeframe(tf)['Overall']
            if tf_status in status_count:
                status_count[tf_status] += 1

        majority_status = max(status_count, key=status_count.get)
        return majority_status if status_count[majority_status] > sum(status_count.values()) / 2 else 'neutral'


    def evaluate_majority_status(self, statuses):
        status_count = {'positive': 0, 'neutral': 0, 'negative': 0}
        for status in statuses:
            status_count[status] += 1
        majority = max(status_count, key=status_count.get)
        return majority if status_count[majority] > len(statuses) / 2 else 'neutral'
    
    def backtest(self, initial_capital=10000):
        """
        Perform a backtest on the historical data using the trading signals generated
        by the framework's evaluation logic.

        Args:
        - initial_capital (float): The starting capital for the backtest.

        Returns:
        A vectorbt Portfolio object containing the results of the backtest.
        """
        price_data = self.timeframes[list(self.timeframes.keys())[0]]['data']
        signals = pd.DataFrame(index=price_data.index, columns=['buy', 'sell'])

        holding = False  

        for i in range(len(price_data)):
            for tf_name in self.timeframes.keys():
                self.timeframes[tf_name]['data'] = price_data.iloc[:i+1]
            
            overall_status = self.determine_overall_status(self.bias_timeframes, self.confirmation_timeframes)
            
            if overall_status == 'positive' and not holding:
                signals.at[price_data.index[i], 'buy'] = True
                holding = True
            elif overall_status == 'negative' and holding:
                signals.at[price_data.index[i], 'sell'] = True
                holding = False
            # No explicit action for 'neutral' or when holding status doesn't change

        # Backtest using vectorbt
        close_prices = price_data['close']
        portfolio = vbt.Portfolio.from_signals(close_prices, signals['buy'].fillna(False), signals['sell'].fillna(False), init_cash=initial_capital)
        
        return portfolio