# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame
from typing import Optional, Union
from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IStrategy, IntParameter)

# --------------------------------
# Add your lib to import here
from functools import reduce
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


# This class is a sample. Feel free to customize it.
class UTBot_Alerts(IStrategy):
    """
    This is a sample strategy to inspire you.
    More information in https://www.freqtrade.io/en/latest/strategy-customization/

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
    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 3

    # Can this strategy go short?
    can_short: bool = False

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    minimal_roi = {
        "60": 0.01,
        "30": 0.02,
        "0": 0.04
    }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = -0.10

    # Trailing stoploss
    trailing_stop = False
    # trailing_only_offset_is_reached = False
    # trailing_stop_positive = 0.01
    # trailing_stop_positive_offset = 0.0  # Disabled / not configured

    # Optimal timeframe for the strategy.
    timeframe = '5m'

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = True

    # These values can be overridden in the config.
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Hyperoptable parameters
    buy_rsi = IntParameter(low=1, high=50, default=30, space='buy', optimize=True, load=True)
    sell_rsi = IntParameter(low=50, high=100, default=70, space='sell', optimize=True, load=True)
    short_rsi = IntParameter(low=51, high=100, default=70, space='sell', optimize=True, load=True)
    exit_short_rsi = IntParameter(low=1, high=50, default=30, space='buy', optimize=True, load=True)

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 200

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

    plot_config = {
        'main_plot': {
            'tema': {},
            'sar': {'color': 'white'},
        },
        'subplots': {
            "MACD": {
                'macd': {'color': 'blue'},
                'macdsignal': {'color': 'orange'},
            },
            "RSI": {
                'rsi': {'color': 'red'},
            }
        }
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
        return []
    def optimize_trend_alert(dataframe, key_value=1, atr_period=3, ema_period=200):

        # Calculate ATR and xATRTrailingStop
        xATR = np.array(ta.ATR(dataframe['high'], dataframe['low'], dataframe['close'], timeperiod=atr_period))
        nLoss = key_value * xATR
        src = dataframe['close']

        # Initialize arrays
        xATRTrailingStop = np.zeros(len(dataframe))
        xATRTrailingStop[0] = src[0] - nLoss[0]

        # Calculate xATRTrailingStop using vectorized operations
        mask_1 = (src > np.roll(xATRTrailingStop, 1)) & (np.roll(src, 1) > np.roll(xATRTrailingStop, 1))
        mask_2 = (src < np.roll(xATRTrailingStop, 1)) & (np.roll(src, 1) < np.roll(xATRTrailingStop, 1))
        mask_3 = src > np.roll(xATRTrailingStop, 1)

        xATRTrailingStop = np.where(mask_1, np.maximum(np.roll(xATRTrailingStop, 1), src - nLoss), xATRTrailingStop)
        xATRTrailingStop = np.where(mask_2, np.minimum(np.roll(xATRTrailingStop, 1), src + nLoss), xATRTrailingStop)
        xATRTrailingStop = np.where(mask_3, src - nLoss, xATRTrailingStop)

        # Calculate pos using vectorized operations
        mask_buy = (np.roll(src, 1) < xATRTrailingStop) & (src > np.roll(xATRTrailingStop, 1))
        mask_sell = (np.roll(src, 1) > xATRTrailingStop)  & (src < np.roll(xATRTrailingStop, 1))

        pos = np.zeros(len(dataframe))
        pos = np.where(mask_buy, 1, pos)
        pos = np.where(mask_sell, -1, pos)
        pos[~((pos == 1) | (pos == -1))] = 0

        ema = np.array(ta.EMA(dataframe['close'], timeperiod=ema_period))

        buy_condition_utbot = (xATRTrailingStop > ema) & (pos > 0) & (src > ema)
        sell_condition_utbot = (xATRTrailingStop < ema) & (pos < 0) & (src < ema)    

        trend = np.where(buy_condition_utbot, 1, np.where(sell_condition_utbot, -1, 0))

        trend = np.array(trend)

        dataframe['trend'] = trend
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        if not self.dp:
            # Don't do anything if DataProvider is not available.
            return dataframe


        L_optimize_trend_alert  = self.optimize_trend_alert(dataframe=dataframe, key_value= self.key_value_l.value, atr_period= self.atr_period_l.value, ema_period=self.ema_period_l.value)
        dataframe['trend_l'] = L_optimize_trend_alert['trend']

        S_optimize_trend_alert  = self.optimize_trend_alert(dataframe=dataframe, key_value= self.key_value_s.value, atr_period= self.atr_period_s.value, ema_period=self.ema_period_s.value)
        dataframe['trend_s'] = S_optimize_trend_alert['trend']

        # ADX
        dataframe['adx'] = ta.ADX(dataframe)
        
        # RSI
        # dataframe['rsi'] = ta.RSI(dataframe)

        # EMA
        dataframe['ema_l'] = ta.EMA(dataframe['close'], timeperiod=self.ema_period_l_exit.value)
        dataframe['ema_s'] = ta.EMA(dataframe['close'], timeperiod=self.ema_period_s_exit.value)


        # Volume Weighted
        dataframe['volume_mean'] = dataframe['volume'].rolling(self.volume_check.value).mean().shift(1)
        dataframe['volume_mean_exit'] = dataframe['volume'].rolling(self.volume_check_exit.value).mean().shift(1)

        dataframe['volume_mean_s'] = dataframe['volume'].rolling(self.volume_check_s.value).mean().shift(1)
        dataframe['volume_mean_exit_s'] = dataframe['volume'].rolling(self.volume_check_exit_s.value).mean().shift(1)




        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        dataframe.loc[
            (
                        (dataframe['adx'] > self.adx_long_min.value) & # trend strength confirmation
                        (dataframe['adx'] < self.adx_long_max.value) & # trend strength confirmation
                        (dataframe['trend_l'] > 0) &
                        (dataframe['volume'] > dataframe['volume_mean']) &
                        (dataframe['volume'] > 0)

            ),
            'enter_long'] = 1

        dataframe.loc[
            (
                        (dataframe['adx'] > self.adx_short_min.value) & # trend strength confirmation
                        (dataframe['adx'] < self.adx_short_max.value) & # trend strength confirmation
                        (dataframe['trend_s'] < 0) &
                        (dataframe['volume'] > dataframe['volume_mean_s']) # volume weighted indicator
            ),
            'enter_short'] = 1
        
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        conditions_long = []
        conditions_short = []
        dataframe.loc[:, 'exit_tag'] = ''

        exit_long = (
                # (dataframe['close'] < dataframe['low'].shift(self.sell_shift.value)) &
                (dataframe['close'] < dataframe['ema_l']) &
                (dataframe['volume'] > dataframe['volume_mean_exit'])
        )

        exit_short = (
                # (dataframe['close'] > dataframe['high'].shift(self.sell_shift_short.value)) &
                (dataframe['close'] > dataframe['ema_s']) &
                (dataframe['volume'] > dataframe['volume_mean_exit_s'])
        )


        conditions_short.append(exit_short)
        dataframe.loc[exit_short, 'exit_tag'] += 'exit_short'


        conditions_long.append(exit_long)
        dataframe.loc[exit_long, 'exit_tag'] += 'exit_long'


        if conditions_long:
            dataframe.loc[
                reduce(lambda x, y: x | y, conditions_long),
                'exit_long'] = 1

        if conditions_short:
            dataframe.loc[
                reduce(lambda x, y: x | y, conditions_short),
                'exit_short'] = 1
        return dataframe
