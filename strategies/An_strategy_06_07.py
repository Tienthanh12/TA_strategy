# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
import numpy as np
import pandas as pd
from typing import Dict, List
from pandas import DataFrame
from technical import qtpylib
from datetime import datetime
from typing import Optional, Union
from freqtrade.optimize.space import Categorical, Dimension, Integer, SKDecimal
from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IntParameter, IStrategy, merge_informative_pair)

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import pandas_ta as pta

# from freqtrade.technical.technical import qtpylib


class An_strategy_06_07(IStrategy):
    """
    This is a strategy template to get you started.
    More information in https://www.freqtra                                                                     de.io/en/latest/strategy-customization/

    You can:
        :return: a Dataframe with all mandatory indicators for the strategies
    - Rename the class name (Do not forget to update class_name)
    - Add any methods you want to build your strategy
    - Add any lib you need to build your strategy

    You must keep:
    - the lib in the section "Do not remove these libs"
    - the methods: populate_indicators, populate_entry_trend, populate_exit_trend
    You should keep:
    - timeframe, minimal_roi, stoploss, trailing_*
    """
    class HyperOpt:
        # Define a custom stoploss space.
        def stoploss_space():
            return [SKDecimal(-1, -0.01, decimals=3, name='stoploss')]

        # Define custom ROI space
        def roi_space() -> List[Dimension]:
            return [
                Integer(10, 1000, name='roi_t1'),
                Integer(10, 1500, name='roi_t2'),
                Integer(10, 3500, name='roi_t3'),
                SKDecimal(0.005, 0.05, decimals=3, name='roi_p1'),
                SKDecimal(0.03, 0.15, decimals=3, name='roi_p2'),
                SKDecimal(0.05, 0.30, decimals=3, name='roi_p3'),
            ]

        def generate_roi_table(params: dict) -> Dict[int, float]:

            roi_table = {}
            roi_table[0] = params['roi_p1'] + params['roi_p2'] + params['roi_p3']
            roi_table[params['roi_t3']] = params['roi_p1'] + params['roi_p2']
            roi_table[params['roi_t3'] + params['roi_t2']] = params['roi_p1']
            roi_table[params['roi_t3'] + params['roi_t2'] + params['roi_t1']] = 0

            return roi_table

        def trailing_space() -> list[Dimension]:
            # All parameters here are mandatory, you can only modify their type or the range.
            return [
                # Fixed to true, if optimizing trailing_stop we assume to use trailing stop at all times.
                Categorical([True], name='trailing_stop'),

                SKDecimal(0.01, 0.35, decimals=3, name='trailing_stop_positive'),
                # 'trailing_stop_positive_offset' should be greater than 'trailing_stop_positive',
                # so this intermediate parameter is used as the value of the difference between
                # them. The value of the 'trailing_stop_positive_offset' is constructed in the
                # generate_trailing_params() method.
                # This is similar to the hyperspace dimensions used for constructing the ROI tables.
                SKDecimal(0.001, 0.1, decimals=3, name='trailing_stop_positive_offset_p1'),

                Categorical([True, False], name='trailing_only_offset_is_reached'),
        ]

        # Define a custom max_open_trades space
        def max_open_trades_space(self) -> List[Dimension]:
            return [
                Integer(-1, 10, name='max_open_trades'),
            ]
    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 3

    # Optimal timeframe for the strategy.
    timeframe = '5m'

    # Can this strategy go short?
    can_short: bool = True

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    minimal_roi = {
        "0": 0.143, 
        "3478": 0.092, 
        "4654":  0.014, 
        "5496": 0    
    }
    stoploss = -0.137
    # Trailing stoploss
    trailing_stop = False
    # trailing_only_offset_is_reached = False
    # trailing_stop_positive = 0.01
    # trailing_stop_positive_offset = 0.0  # Disabled / not configured

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = True

    # These values can be overridden in the config.
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 400

    # Optional order type mapping.
    order_types = {
        'entry': 'limit',
        'exit': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    # Optional order time in force.
    order_time_in_force = {
        'entry': 'GTC',
        'exit': 'GTC'
    }
    

    def informative_pairs(self):
        """
        Define additional, informative pair/interval combinations to be cached from the exchange.
        These pair/interval combinations are non-tradeable, unless they are part
        of the whitelist as well.
        For more information, please consult the documentation
        :return: List of tuples in the format (pair, interval)
            Sample: return [("ETH/USDT", "5m"),
                            ("BTC/USDT", "15m"),
                            ]
        """
        return [
            ("BTC/USDT:USDT", "1h"),
             ]
    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float, entry_tag: Optional[str], side: str,
                 **kwargs) -> float:
        """
        Customize leverage for each new trade. This method is only called in futures mode.

        :param pair: Pair that's currently analyzed
        :param current_time: datetime object, containing the current datetime
        :param current_rate: Rate, calculated based on pricing settings in exit_pricing.
        :param proposed_leverage: A leverage proposed by the bot.
        :param max_leverage: Max leverage allowed on this pair
        :param entry_tag: Optional entry_tag (buy_tag) if provided with the buy signal.
        :param side: 'long' or 'short' - indicating the direction of the proposed trade
        :return: A leverage amount, which is between 1.0 and max_leverage.
        """
        return 1
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Adds several different TA indicators to the given DataFrame

        Performance Note: For the best performance be frugal on the number of indicators
        you are using. Let uncomment only the indicator you are using in your strategies
        or your hyperopt configuration, otherwise you will waste your memory and CPU usage.
        :param dataframe: Dataframe with data from the exchange
        :param metadata: Additional information, like the currently traded pair
        :return: a Dataframe with all mandatory indicators for the strategies
        """
        
        if not self.dp:
            # Don't do anything if DataProvider is not available.
            return dataframe

        #### TREND ####
        inf_tf = '1h'
        informative = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe=inf_tf)    
        # Get the 200 hour ma
        informative['ma200'] = ta.MA(informative, timeperiod=200)

        # Support and Resistance for 1h
        supports_1h, resistances_1h = self.supports_and_resistances(informative, 70, field_for_support='low', field_for_resistance='high')
        informative['support'] = None
        informative.loc[supports_1h.index, "support"] = supports_1h.values
        informative['resistance'] = None
        informative.loc[resistances_1h.index, "resistance"] = resistances_1h.values
        informative['date'] = pd.to_datetime(informative['date'])

        # Xét từng nến để tìm các Resistance/Support gần nhất
        informative['nearest_support_index'] = -1
        informative['nearest_support'] = -1
        informative['nearest_resistance_index'] = -1
        informative['nearest_resistance'] = -1

        # Duyệt qua từng hàng trong DataFrame
        for i in range(len(informative)):

            # Lấy giá đóng cửa của nến hiện tại
            close_price = informative.loc[i, 'close']

            nearest_support_1h = supports_1h[supports_1h.index < i]
            nearest_resistance_1h = resistances_1h[resistances_1h.index < i]

            # Tìm mức hỗ trợ gần nhất (nhỏ hơn giá đóng cửa của nến)
            nearest_support_1h_index = nearest_support_1h[nearest_support_1h.values < close_price].index.max()
            if not pd.isna(nearest_support_1h_index):
                informative.loc[i, 'nearest_support_index'] = nearest_support_1h_index 
                informative.loc[i, 'nearest_support'] = nearest_support_1h[nearest_support_1h_index]

            # Tìm mức kháng cự gần nhất (lớn hơn giá đóng cửa của nến)
            nearest_resistance_1h_index = nearest_resistance_1h[nearest_resistance_1h.values > close_price].index.max()
            if not pd.isna(nearest_resistance_1h_index):
                informative.loc[i, 'nearest_resistance_index'] = nearest_resistance_1h_index 
                informative.loc[i, 'nearest_resistance'] = nearest_resistance_1h[nearest_resistance_1h_index]    
        dataframe = merge_informative_pair(dataframe, informative, self.timeframe, inf_tf, ffill=True)

        ### AREA OF VALUE & ENTRY TRIGER ###
        # Price channel    
        dataframe = self.trendlines(dataframe=dataframe, slicing_window=70, distance=30, chart=True, field_for_supports='low', field_for_resistances='high', timeframe='5m')
        
        # Shift values of maxslope, minslope, max_y_intercept, min_y_intercept of previous hour to prior hour
        dataframe['previous_maxslope_5m'] = dataframe['maxslope_5m'].shift(1)
        dataframe['previous_minslope_5m'] = dataframe['minslope_5m'].shift(1)
        dataframe['previous_max_y_intercept_5m'] = dataframe['max_y_intercept_5m'].shift(1)
        dataframe['previous_min_y_intercept_5m'] = dataframe['min_y_intercept_5m'].shift(1)

        # Peak and Bottom for 5m
        # bottoms_5m, peaks_5m = self.supports_and_resistances(dataframe, 50, field_for_support='low', field_for_resistance='high')
        # dataframe['bottom_5m'] = None
        # dataframe.loc[bottoms_5m.index, "bottom_5m"] = bottoms_5m.values
        # dataframe['peak_5m'] = None
        # dataframe.loc[peaks_5m.index, "peak_5m"] = peaks_5m.values
        # dataframe['date'] = pd.to_datetime(dataframe['date'])

        # # Xét từng nến để tìm các đỉnh/đáy gần nhất
        # dataframe['nearest_peak_index_5m'] = -1
        # dataframe['nearest_peak_5m'] = -1
        # dataframe['nearest_bottom_index_5m'] = -1
        # dataframe['nearest_bottom_5m'] = -1

        # # Duyệt qua từng hàng trong DataFrame
        # for i in range(len(dataframe)):

        #     # Lấy giá đóng cửa của nến hiện tại
        #     close_price = dataframe.loc[i, 'close']

        #     # Tìm chỉ số (indice) của mức đáy và mức đỉnh gần nhất
        #     nearest_bottom_5m = bottoms_5m[bottoms_5m.index < i]
        #     if len(nearest_bottom_5m) != 0:
        #         dataframe.loc[i, 'nearest_bottom_index_5m'] = nearest_bottom_5m.index.max()
        #         dataframe.loc[i, 'nearest_bottom_5m'] = nearest_bottom_5m[nearest_bottom_5m.index.max()]

        #     nearest_peak_5m = peaks_5m[peaks_5m.index < i]
        #     if len(nearest_peak_5m) != 0:
        #         dataframe.loc[i, 'nearest_peak_index_5m'] = nearest_peak_5m.index.max()
        #         dataframe.loc[i, 'nearest_peak_5m'] = nearest_peak_5m[nearest_peak_5m.index.max()]

        # Xét từng nến để tìm các đỉnh/đáy, vùng kháng cự/ hỗ trợ gần nhất
        dataframe['previous_nearest_support_1h'] = dataframe['nearest_support_1h']
        dataframe['previous_nearest_resistance_1h'] = dataframe['nearest_resistance_1h']
        # dataframe['previous_nearest_peak_5m'] = dataframe['nearest_peak_5m'].shift(1)
        # dataframe['previous_nearest_bottom_5m'] = dataframe['nearest_bottom_5m'].shift(1)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the entry signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with entry columns populated
        """
        dataframe.loc[
            (
                (
                    dataframe['close'] > dataframe['previous_maxslope_5m'] * dataframe['close'].index + dataframe['previous_max_y_intercept_5m']
                )
                &
                (
                    (dataframe['close'] - (dataframe['previous_maxslope_5m'] * dataframe['close'].index + dataframe['previous_max_y_intercept_5m'])) >= (dataframe['close'] - dataframe['open'])*1/2
                )
                &
                (
                    dataframe['previous_maxslope_5m'] > -6
                )
                &
                (
                    dataframe['previous_maxslope_5m'] < 6
                )
                &
                (
                    dataframe['previous_minslope_5m'] < 5.4
                )
                &
                (
                    dataframe['previous_minslope_5m'] > -5.4
                )
                &
                (   
                    dataframe['close_1h'] > dataframe['ma200_1h']
                ) 
            ),
            'enter_long',
        ] = 1

        dataframe.loc[
            (
                (
                    dataframe['close'] < dataframe['previous_minslope_5m'] * dataframe['close'].index + dataframe['previous_min_y_intercept_5m']
                )
                &
                (
                    (dataframe['close'] - (dataframe['previous_minslope_5m'] * dataframe['close'].index + dataframe['previous_min_y_intercept_5m'])) <= (dataframe['close'] - dataframe['open'])*1/2
                )
                &
                # (
                #     dataframe['open'] < dataframe['previous_maxslope_5m'] * dataframe['close'].index + dataframe['previous_max_y_intercept_5m']
                # )
                # &
                (
                    dataframe['previous_maxslope_5m'] > -6
                )
                &
                (
                    dataframe['previous_maxslope_5m'] < 6
                )
                &
                (
                    dataframe['previous_minslope_5m'] < 5.4
                )
                &
                (
                    dataframe['previous_minslope_5m'] > -5.4
                )
                &
                (   
                    dataframe['close_1h'] < dataframe['ma200_1h']
                ) 
            ),
            'enter_short',
        ] = 1
        # dataframe.to_csv("./user_data/backtesting.csv")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (
                    dataframe['previous_nearest_resistance_1h'] != -1
                ) &
                (
                    (
                        dataframe['close'] >= dataframe['previous_nearest_resistance_1h'] - 300
                    )  
                    &
                    (
                        dataframe['close'] <= dataframe['previous_nearest_resistance_1h'] + 300
                    ) 
                #     # (
                #     #     dataframe['close'] <= dataframe['previous_nearest_bottom_5m']
                #     # )
                )
            ),
            'exit_long'] = 1
        
        dataframe.loc[
            (
                (
                    dataframe['previous_nearest_support_1h'] != -1
                ) &
                (
                    (
                        dataframe['close'] >= dataframe['previous_nearest_support_1h'] - 300
                    )  
                    &
                    (
                        dataframe['close'] <= dataframe['previous_nearest_support_1h'] + 300
                    ) 
                #     # (
                #     #     dataframe['close'] <= dataframe['previous_nearest_bottom_5m']
                #     # )
                )
            ),
            'exit_short'] = 1

        dataframe.to_csv("./user_data/result_backtest_new.csv")
        return dataframe

    """
    Put other function for our own strategy in here
    """
    def trendlines(self,dataframe, slicing_window=100, distance=50, chart=True, field_for_supports='low', field_for_resistances='high', timeframe="1h"):

        supports, resistances = self.supports_and_resistances_trendlines(dataframe, 20, field_for_support='low', field_for_resistance='high')
        dataframe['support_trendlines'] = 100000
        dataframe.loc[supports.index, "support_trendlines"] = supports.values
        dataframe['resistance_trendlines'] = -1
        dataframe.loc[resistances.index, "resistance_trendlines"] = resistances.values
        # Step 1: Using rolling window to find 2 peaks and 2 bottoms in each 100 candles
        df_high = dataframe['resistance_trendlines']
        df_low = dataframe['support_trendlines']

        dataframe['peak1_idx'] = df_high.rolling(window=slicing_window).apply(lambda x: x.idxmax())
        dataframe['bottom1_idx'] = df_low.rolling(window=slicing_window).apply(lambda x: x.idxmin())
        dataframe['peak2_idx'] = df_high.rolling(window=slicing_window).apply(self.find_second_peak, args=(dataframe[field_for_resistances], distance,))
        dataframe['bottom2_idx'] = df_low.rolling(window=slicing_window).apply(self.find_second_bottom, args=(dataframe[field_for_supports], distance,))
        
        # Step 2: Find maxline through 2 peaks and minline through 2 bottoms in each 100 candles
        dataframe['maxslope_' + timeframe] = None
        dataframe.loc[slicing_window - 1:, 'maxslope_' + timeframe] = (np.array(dataframe[field_for_resistances].iloc[dataframe['peak1_idx'][slicing_window - 1:].astype(int)]) - 
                                                    np.array(dataframe[field_for_resistances].iloc[dataframe['peak2_idx'][slicing_window - 1:].astype(int)])) / (np.array(dataframe['peak1_idx'][slicing_window - 1:]) - 
                                                                                                                                            np.array(dataframe['peak2_idx'][slicing_window - 1:])) # Slope between max points
        
        dataframe['minslope_' + timeframe] = None
        dataframe.loc[slicing_window - 1:, 'minslope_' + timeframe] = (np.array(dataframe[field_for_supports].iloc[dataframe['bottom1_idx'][slicing_window - 1:].astype(int)]) - 
                                                    np.array(dataframe[field_for_supports].iloc[dataframe['bottom2_idx'][slicing_window - 1:].astype(int)])) / (np.array(dataframe['bottom1_idx'][slicing_window - 1:]) - 
                                                                                                                                            np.array(dataframe['bottom2_idx'][slicing_window - 1:])) # Slope between max points

        dataframe['max_y_intercept_' + timeframe] = None
        dataframe.loc[slicing_window - 1:, 'max_y_intercept_' + timeframe] = (np.array(dataframe[field_for_resistances].iloc[dataframe['peak1_idx'][slicing_window - 1:].astype(int)]) - 
                                                            np.array(dataframe['maxslope_' + timeframe][slicing_window - 1:]) * np.array(dataframe['peak1_idx'][slicing_window - 1:])) # y-intercept for max trendline
        dataframe['min_y_intercept_' + timeframe] = None
        dataframe.loc[slicing_window - 1:, 'min_y_intercept_' + timeframe] = (np.array(dataframe[field_for_supports].iloc[dataframe['bottom1_idx'][slicing_window - 1:].astype(int)]) - 
                                                            np.array(dataframe['minslope_' + timeframe][slicing_window - 1:]) * np.array(dataframe['bottom1_idx'][slicing_window - 1:])) # y-intercept for min trendline
        return dataframe
    
    def find_second_peak(self, window_data, df_high, distance):
        window_data_high = df_high.loc[df_high.index]
        peak1_idx = window_data.idxmax()
        if (peak1_idx + distance >= window_data.index[-1]):    
            peak2_idxx = window_data.loc[: (peak1_idx - distance + 1)].idxmax()
        else:
            peak2_idxx = window_data.loc[(peak1_idx + distance) :].idxmax()
        if window_data.loc[peak2_idxx] > 0:
            peak2_idx = peak2_idxx
        else:
            if (peak1_idx + distance >= window_data_high.index[-1]):    
                peak2_idx = window_data_high.loc[: (peak1_idx - distance + 1)].idxmax()
            else:
                peak2_idx = window_data_high.loc[(peak1_idx + distance) :].idxmax()
        return peak2_idx


    def find_second_bottom(self, window_data, df_low, distance):
        window_data_low = df_low.loc[window_data.index]
        bottom1_idx = window_data.idxmin()
        if bottom1_idx + distance >= window_data.index[-1]:    
            bottom2_idxx = window_data.loc[: (bottom1_idx - distance + 1)].idxmin()
        else:
            bottom2_idxx = window_data.loc[(bottom1_idx + distance) :].idxmin()
        if window_data.loc[bottom2_idxx] < 100000:
            bottom2_idx = bottom2_idxx
        else:
            if bottom1_idx + distance >= window_data_low.index[-1]:    
                bottom2_idx = window_data_low.loc[: (bottom1_idx - distance + 1)].idxmin()
            else:
                bottom2_idx = window_data_low.loc[(bottom1_idx + distance) :].idxmin()
        return bottom2_idx
    
    # def trendlines(self, dataframe, slicing_window=100, distance=50, chart=True, field_for_supports='low', field_for_resistances='high', timeframe="1h"):
    #     """
    #     Return a Pandas dataframe with support and resistance lines.

    #     :param dataframe: incoming data matrix
    #     :param slicing_window: number of candles for slicing window
    #     :param distance: Number of candles between two maximum points and two minimum points
    #     :param chart: Boolean value saying whether to print chart on web
    #     :param field_for_supports: for which column would you like to generate the support lines
    #     :param field_for_resistances: for which column would you like to generate the resistance lines
    #     :param timeframe: tmieframe use to find trendline
    #     """

    #     # Step 1: Using rolling window to find 2 peaks and 2 bottoms in each 100 candles
    #     df_high = dataframe[field_for_resistances].copy()
    #     df_low = dataframe[field_for_supports].copy()

    #     dataframe['peak1_idx'] = df_high.rolling(window=slicing_window).apply(lambda x: x.idxmax())
    #     dataframe['bottom1_idx'] = df_low.rolling(window=slicing_window).apply(lambda x: x.idxmin())
    #     dataframe['peak2_idx'] = df_high.rolling(window=slicing_window).apply(self.find_second_peak, args=(distance, ))
    #     dataframe['bottom2_idx'] = df_low.rolling(window=slicing_window).apply(self.find_second_bottom, args=(distance, ))
        
    #     # Step 2: Find maxline through 2 peaks and minline through 2 bottoms in each 100 candles
    #     dataframe['maxslope_' + timeframe] = None
    #     dataframe.loc[slicing_window - 1:, 'maxslope_' + timeframe] = (np.array(dataframe[field_for_resistances].iloc[dataframe['peak1_idx'][slicing_window - 1:].astype(int)]) - 
    #                                                 np.array(dataframe[field_for_resistances].iloc[dataframe['peak2_idx'][slicing_window - 1:].astype(int)])) / (np.array(dataframe['peak1_idx'][slicing_window - 1:]) - 
    #                                                                                                                                         np.array(dataframe['peak2_idx'][slicing_window - 1:])) # Slope between max points
        
    #     dataframe['minslope_' + timeframe] = None
    #     dataframe.loc[slicing_window - 1:, 'minslope_' + timeframe] = (np.array(dataframe[field_for_supports].iloc[dataframe['bottom1_idx'][slicing_window - 1:].astype(int)]) - 
    #                                                 np.array(dataframe[field_for_supports].iloc[dataframe['bottom2_idx'][slicing_window - 1:].astype(int)])) / (np.array(dataframe['bottom1_idx'][slicing_window - 1:]) - 
    #                                                                                                                                         np.array(dataframe['bottom2_idx'][slicing_window - 1:])) # Slope between max points

    #     dataframe['max_y_intercept_' + timeframe] = None
    #     dataframe.loc[slicing_window - 1:, 'max_y_intercept_' + timeframe] = (np.array(dataframe[field_for_resistances].iloc[dataframe['peak1_idx'][slicing_window - 1:].astype(int)]) - 
    #                                                         np.array(dataframe['maxslope_' + timeframe][slicing_window - 1:]) * np.array(dataframe['peak1_idx'][slicing_window - 1:])) # y-intercept for max trendline
    #     dataframe['min_y_intercept_' + timeframe] = None
    #     dataframe.loc[slicing_window - 1:, 'min_y_intercept_' + timeframe] = (np.array(dataframe[field_for_supports].iloc[dataframe['bottom1_idx'][slicing_window - 1:].astype(int)]) - 
    #                                                         np.array(dataframe['minslope_' + timeframe][slicing_window - 1:]) * np.array(dataframe['bottom1_idx'][slicing_window - 1:])) # y-intercept for min trendline
            
    #     return dataframe

    
    # def find_second_peak(self, window_data, distance):
    #     peak1_idx = window_data.idxmax()
    #     if peak1_idx + distance >= window_data.index[-1]:    
    #         peak2_idx = window_data.loc[: (peak1_idx - distance + 1)].idxmax()
    #     else:
    #         peak2_idx = window_data.loc[(peak1_idx + distance) :].idxmax()
    #     return peak2_idx


    # def find_second_bottom(self, window_data, distance):
    #     bottom1_idx = window_data.idxmin()
    #     if bottom1_idx + distance >= window_data.index[-1]:    
    #         bottom2_idx = window_data.loc[: (bottom1_idx - distance + 1)].idxmin()
    #     else:
    #         bottom2_idx = window_data.loc[(bottom1_idx + distance) :].idxmin()
    #     return bottom2_idx
    def supports_and_resistances(self, dataframe, rollsize, field_for_support='low', field_for_resistance='high'): 
        diffs1 = abs(dataframe['high'].diff().abs().iloc[1:]) 

        diffs2 = abs(dataframe['low'].diff().abs().iloc[1:]) 

        mean_deviation_ressistance = diffs1.mean() 

        mean_deviation_support = diffs2.mean() 
        supports = dataframe[dataframe.low == dataframe[field_for_support].rolling(rollsize, center=True).min()].low
        resistances = dataframe[dataframe.high == dataframe[field_for_resistance].rolling(rollsize, center=True).max()].high
        supports = supports[abs(supports.diff()) > mean_deviation_support] 
        resistances = resistances[abs(resistances.diff()) > mean_deviation_ressistance] 
        return supports,resistances 
    
    def supports_and_resistances_trendlines(self, dataframe, rollsize, field_for_support='low', field_for_resistance='high'): 
        diffs1 = abs(dataframe['high'].diff().abs().iloc[1:]) 

        diffs2 = abs(dataframe['low'].diff().abs().iloc[1:]) 

        # mean_deviation_ressistance = diffs1.mean() 

        # mean_deviation_support = diffs2.mean() 
        supports = dataframe[dataframe.low == dataframe[field_for_support].rolling(rollsize, center=True).min()].low
        resistances = dataframe[dataframe.high == dataframe[field_for_resistance].rolling(rollsize, center=True).max()].high
        # supports = supports[abs(supports.diff()) > mean_deviation_support] 
        # resistances = resistances[abs(resistances.diff()) > mean_deviation_ressistance] 
        return supports,resistances 
