def generate_signal_score(df, column_name, signal_line=None, threshold_up=None, threshold_down=None, neutral_zone=None, inverted=False):
    """
    Generates a signal based on the analysis of a single column within a DataFrame.
    The signal can be based on threshold crossing, crossover signals, or within a neutral zone.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing the data series to be analyzed.
    - column_name (str): Column name in `df` to generate the signal for.
    - signal_line (str, optional): The column name to be used as a signal line for crossover comparison.
    - threshold_up (float, optional): The upper threshold value for generating a 'positive' signal.
    - threshold_down (float, optional): The lower threshold value for generating a 'negative' signal.
    - neutral_zone (tuple, optional): A tuple of (lower_bound, upper_bound) defining the neutral zone range.
    - inverted (bool, optional): If True, inverts the interpretation of 'positive' and 'negative' signals.

    Returns:
    str: The generated signal ('positive', 'negative', 'neutral') based on the latest data point in `column_name`.
    """
    
    if column_name not in df or df[column_name].isna().iloc[-1]:
        return 'neutral' 
    
    latest_value = df[column_name].iloc[-1]
    
    if signal_line:
        if signal_line not in df or df[signal_line].isna().iloc[-1]:
            return 'neutral'  
        
        tolerance = neutral_zone if neutral_zone else 0
        signal_line_value = df[signal_line].iloc[-1]
        
        if (latest_value > (signal_line_value + tolerance)) ^ inverted:
            return 'negative' if inverted else 'positive'
        elif (latest_value < (signal_line_value - tolerance)) ^ inverted:
            return 'positive' if inverted else 'negative'
        else:
            return 'neutral'
    else:
        if neutral_zone:
            lower_bound, upper_bound = neutral_zone
            if (latest_value > threshold_up) ^ inverted:
                return 'negative' if inverted else 'positive'
            elif (latest_value < threshold_down) ^ inverted:
                return 'positive' if inverted else 'negative'
            elif lower_bound <= latest_value <= upper_bound:
                return 'neutral'
            else:
                return 'neutral'
        else:
            if (latest_value > threshold_up) ^ inverted:
                return 'negative' if inverted else 'positive'
            elif (latest_value < threshold_down) ^ inverted:
                return 'positive' if inverted else 'negative'
            else:
                return 'neutral'
            
class Signal:
    """
    Represents a single trading signal within a trading strategy or framework.

    Attributes:
    - name (str): The name of the signal.
    - eval_function (callable): The function used to evaluate the signal. Should accept a DataFrame as input and return a signal ('positive', 'negative', 'neutral').
    - chart (bool): Indicates if the signal should be visualized on a chart.
    - subplot (bool): Indicates if the signal visualization should be on a separate subplot.

    Methods:
    - evaluate(df): Evaluates the signal based on the provided DataFrame using `eval_function`.
    """
    def __init__(self, name, eval_function, chart=False, subplot=False):
        self.name = name
        self.eval_function = eval_function
        self.chart = chart
        self.subplot = subplot

    def evaluate(self, df):
        """
        Evaluates the signal based on the provided DataFrame.

        Parameters:
        - df (pd.DataFrame): The DataFrame to evaluate the signal on.

        Returns:
        str: The result of the signal evaluation ('positive', 'negative', 'neutral').
        """
        return self.eval_function(df)
    

class SignalGroup:
    """
    Represents a group of trading signals, allowing for aggregate analysis and evaluation.

    Attributes:
    - name (str): The name of the signal group.
    - signals (list): A list of Signal objects belonging to this group.
    - cached_results (dict): Cached results of the last evaluation to optimize performance.
    - last_calculated (datetime): Timestamp of the last evaluation.

    Methods:
    - add_signal(signal): Adds a Signal object to the signal group.
    - evaluate_group(df, update_timestamp): Evaluates all signals in the group based on the provided DataFrame.
    """
    def __init__(self, name):
        self.name = name
        self.signals = []
        self.cached_results = {}
        self.last_calculated = None

    def add_signal(self, signal):
        self.signals.append(signal)

    def evaluate_group(self, df, update_timestamp=None):
        """
        Evaluates all signals in the group based on the provided DataFrame. Caches the results if the data has not changed since the last evaluation.

        Parameters:
        - df (pd.DataFrame): The DataFrame to evaluate the signals on.
        - update_timestamp (datetime, optional): The timestamp of the data update to check if re-evaluation is necessary.

        Returns:
        dict: A dictionary of signal evaluation results, including the overall status of the signal group.
        """
        if self.cached_results and (self.last_calculated is not None and update_timestamp <= self.last_calculated):
            return self.cached_results
        else:
            self.cached_results = {signal.name: signal.evaluate(df) for signal in self.signals}
            positive_count = sum(status == 'positive' for status in self.cached_results.values())
            negative_count = sum(status == 'negative' for status in self.cached_results.values())
            if positive_count > negative_count:
                self.cached_results['Overall'] = 'positive'
            elif negative_count > positive_count:
                self.cached_results['Overall'] = 'negative'
            else: 
                self.cached_results['Overall'] = 'neutral'

            self.last_calculated = update_timestamp

            return self.cached_results
            
