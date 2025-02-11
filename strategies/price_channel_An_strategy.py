import pandas as pd
import numpy as np
import plotly.graph_objects as go
# import talib.abstract as ta 



def find_second_peak(window_data, distance):
    peak1_idx = window_data.idxmax()
    # print(peak1_idx, distance, window_data.index[-1])
    # print(window_data.index[-1])
    if peak1_idx + distance >= window_data.index[-1]:    
        peak2_idx = window_data.loc[: (peak1_idx - distance + 1)].idxmax()
    else:
        # print(window_data.index[-1])
        peak2_idx = window_data.loc[(peak1_idx + distance) :].idxmax()
    return peak2_idx


def find_second_bottom(window_data, distance):
    bottom1_idx = window_data.idxmin()
    if bottom1_idx + distance >= window_data.index[-1]:    
        bottom2_idx = window_data.loc[: (bottom1_idx - distance + 1)].idxmin()
    else:
        bottom2_idx = window_data.loc[(bottom1_idx + distance) :].idxmin()
    return bottom2_idx


def draw_trendline(dataframe):
        
        # Create Plotly figure
    fig = go.Figure()

    # Candlestick data
    fig = go.Figure(data=[go.Candlestick(x=dataframe.index,
                                          open=dataframe["open"],
                                          high=dataframe["high"],
                                          low=dataframe["low"],
                                          close=dataframe["close"],
                                          name="OHLC")])

    # Plot trendlines
    for i in range(len(dataframe)):
        if i >= 100:  # Start drawing trendlines from the 100th row
            max_slope = dataframe.at[i, 'maxslope']
            max_y_intercept = dataframe.at[i, 'max_y_intercept']
            min_slope = dataframe.at[i, 'minslope']
            min_y_intercept = dataframe.at[i, 'min_y_intercept']

            # Calculate x values for trendlines (100 candles before current row)
            x_values = list(range(i - 99, i))

            # Calculate y values for trendlines
            y_values_max = [max_slope * x + max_y_intercept for x in x_values]
            y_values_min = [min_slope * x + min_y_intercept for x in x_values]

            # Add trendlines to the figure
            fig.add_trace(go.Scatter(x=dataframe.index[i-99:i], y=y_values_max, mode='lines', name=f"Max Trendline {i}"))
            fig.add_trace(go.Scatter(x=dataframe.index[i-99:i], y=y_values_min, mode='lines', name=f"Min Trendline {i}"))

    # Update layout
    fig.update_layout(
        title="Trendlines with Max and Min Slopes and Y-intercepts",
        xaxis_title="Date",
        yaxis_title="Value",
        showlegend=True,
        template="plotly_white"
    )

    # Show plot
    fig.show()


def trendlines(dataframe, slicing_window=100, distance=30, chart=True, field_for_supports='low', field_for_resistances='high', timeframe="1h"):
    """
    Return a Pandas dataframe with support and resistance lines.

    :param dataframe: incoming data matrix
    :param slicing_window: number of candles for slicing window
    :param distance: Number of candles between two maximum points and two minimum points
    :param chart: Boolean value saying whether to print chart on web
    :param field_for_supports: for which column would you like to generate the support lines
    :param field_for_resistances: for which column would you like to generate the resistance lines
    :param timeframe: tmieframe use to find trendline
    """

    # Step 1: Using rolling window to find 2 peaks and 2 bottoms in each 100 candles
    df_high = dataframe[field_for_resistances].copy()
    df_low = dataframe[field_for_supports].copy()

    dataframe['peak1_idx'] = df_high.rolling(window=slicing_window).apply(lambda x: x.idxmax())
    dataframe['bottom1_idx'] = df_low.rolling(window=slicing_window).apply(lambda x: x.idxmin())
    dataframe['peak2_idx'] = df_high.rolling(window=slicing_window).apply(find_second_peak, args=(distance, ))
    dataframe['bottom2_idx'] = df_low.rolling(window=slicing_window).apply(find_second_bottom, args=(distance, ))
    
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

    
    if chart:
        draw_trendline(dataframe)
        
    return dataframe


def supports_and_resistances(dataframe, rollsize, field_for_support='low', field_for_resistance='high'): 
    diffs1 = abs(dataframe['high'].diff().abs().iloc[1:]) 

    diffs2 = abs(dataframe['low'].diff().abs().iloc[1:]) 

    mean_deviation_ressistance = diffs1.mean() 

    mean_deviation_support = diffs2.mean() 
    supports = dataframe[dataframe.low == dataframe[field_for_support].rolling(rollsize, center=True).min()].low 
    resistances = dataframe[dataframe.high == dataframe[field_for_resistance].rolling(rollsize, center=True).max()].high 
    supports = supports[abs(supports.diff()) > mean_deviation_support] 
    resistances = resistances[abs(resistances.diff()) > mean_deviation_ressistance] 
    return supports,resistances 


if __name__ == "__main__":
    
    """
    - Sử dụng file dataframe đã được lưu từ bot đưa vào đường dẫn
    """
    # Read data
    df_5m = pd.read_csv('/home/thanh_ubuntu/freqtrade/user_data/result_backtest_new.csv')[20327:20627]
    start_time = "2023-03-11 07:45:00+00:00"
    end_time = "2023-03-11 12:45:00+00:00"
    entry_time = "2023-03-11 12:55:00+00:00"
    exit_time = "2023-03-13 14:05:00+00:00"
    
    # df_1h = pd.read_csv('/home/huy/user/freqtrade/huytq/test_12_price_channel/data_backtest/btc_1h.csv')
    # df_5m.reset_index(drop=True, inplace=True)
    # df_1h.reset_index(drop=True, inplace=True)
    print(df_5m)

    """
    - Toàn bộ phần này là để chạy code, là các bước tính toán từng phần trong việc tính kênh giá và tìm support và resistance
    """
    """
    # Parameters
    slicing_window = 60
    distance = 20
    rollsize_support_and_resistance = 50
    rollsize_bottom_and_peak = 50

    # # TREND
    # df_5m['200ma'] = ta.MA(df_5m, timeperiod=200)

    # Price channel    
    df_5m = trendlines(dataframe=df_5m, slicing_window=slicing_window, distance=distance, chart=False, field_for_supports='low', field_for_resistances='high', timeframe='5m')


    # Peak and Bottom for 5m
    supports_5m, resistances_5m = supports_and_resistances(df_5m, rollsize_support_and_resistance, field_for_support='low', field_for_resistance='high')
    df_5m['support_5m'] = None
    df_5m.loc[supports_5m.index, "support_5m"] = supports_5m.values
    df_5m['resistance_5m'] = None
    df_5m.loc[resistances_5m.index, "resistance_5m"] = resistances_5m.values
    df_5m['date'] = pd.to_datetime(df_5m['date'])

    # Xét từng nến để tìm các đỉnh/đáy gần nhất
    df_5m['nearest_peak_index_5m'] = -1
    df_5m['nearest_peak_5m'] = -1
    df_5m['nearest_bottom_index_5m'] = -1 
    df_5m['nearest_bottom_5m'] = -1

    # Duyệt qua từng hàng trong DataFrame
    for i in range(len(df_5m)):

        # Lấy giá đóng cửa của nến hiện tại
        close_price = df_5m.loc[i, 'close']

        # Tìm chỉ số (indice) của mức đáy và mức đỉnh gần nhất
        nearest_bottom_5m = supports_5m[supports_5m.index < i]
        if len(nearest_bottom_5m) != 0:
            df_5m.loc[i, 'nearest_bottom_index_5m'] = nearest_bottom_5m.index.max()
            df_5m.loc[i, 'nearest_bottom_5m'] = nearest_bottom_5m[nearest_bottom_5m.index.max()]

        nearest_peak_5m = resistances_5m[resistances_5m.index < i]
        if len(nearest_peak_5m) != 0:
            df_5m.loc[i, 'nearest_peak_index_5m'] = nearest_peak_5m.index.max()
            df_5m.loc[i, 'nearest_peak_5m'] = nearest_peak_5m[nearest_peak_5m.index.max()]


    # Support and Resistance for 1h
    supports_1h, resistances_1h = supports_and_resistances(df_1h, rollsize_bottom_and_peak, field_for_support='low', field_for_resistance='high')
    df_1h['support_1h'] = None
    df_1h.loc[supports_1h.index, "support_1h"] = supports_1h.values
    df_1h['resistance_1h'] = None
    df_1h.loc[resistances_1h.index, "resistance_1h"] = resistances_1h.values
    df_1h['date'] = pd.to_datetime(df_1h['date'])

    # Xét từng nến để tìm các Resistance/Support gần nhất
    df_1h['nearest_support_1h_index'] = -1
    df_1h['nearest_support_1h'] = -1
    df_1h['nearest_resistance_1h_index'] = -1
    df_1h['nearest_resistance_1h'] = -1

    # Duyệt qua từng hàng trong DataFrame
    for i in range(len(df_1h)):

        # Lấy giá đóng cửa của nến hiện tại
        close_price = df_1h.loc[i, 'close']

        nearest_support_1h = supports_1h[supports_1h.index < i]
        nearest_resistance_1h = resistances_1h[resistances_1h.index < i]

        # Tìm mức hỗ trợ gần nhất (nhỏ hơn giá đóng cửa của nến)
        nearest_support_1h_index = nearest_support_1h[nearest_support_1h.values < close_price].index.max()
        if not pd.isna(nearest_support_1h_index):
            df_1h.loc[i, 'nearest_support_1h_index'] = nearest_support_1h_index 
            df_1h.loc[i, 'nearest_support_1h'] = nearest_support_1h[nearest_support_1h_index]
        

        # Tìm mức kháng cự gần nhất (lớn hơn giá đóng cửa của nến)
        nearest_resistance_1h_index = nearest_resistance_1h[nearest_resistance_1h.values > close_price].index.max()
        if not pd.isna(nearest_resistance_1h_index):
            df_1h.loc[i, 'nearest_resistance_1h_index'] = nearest_resistance_1h_index 
            df_1h.loc[i, 'nearest_resistance_1h'] = nearest_resistance_1h[nearest_resistance_1h_index]
    """

    # Visualize thời điểm vào lệnh
    fig = go.Figure(data=[go.Candlestick(x=df_5m['date'],
                                          open=df_5m["open"],
                                          high=df_5m["high"],
                                          low=df_5m["low"],
                                          close=df_5m["close"],
                                          customdata=df_5m["index"],
                                          name="OHLC",      # Dùng text để truyền index vào hover
                                          hovertext='Index: ' + df_5m['index'].astype(str),  # Tạo nội dung hovertext
                                        #   overinfo='text+x+open+high+low+close',  # Hiển thị hovertext kèm theo thông tin x, yh
                                        )])
                                            
                                            
    """
    - Chọn thời điểm bắt đầu và kết thúc của kênh giá, trong đó:
    + Điểm kết thúc là điểm trước thời điểm vào lệnh
    """
    

    start_indice = df_5m[df_5m['date'] == start_time].index[0]
    end_indice = df_5m[df_5m['date'] == end_time].index[0]
    number_candles_to_draw = end_indice - start_indice
    
    max_slope = df_5m['maxslope_5m'][end_indice]
    max_y_intercept = df_5m['max_y_intercept_5m'][end_indice]
    min_slope = df_5m['minslope_5m'][end_indice]
    min_y_intercept = df_5m['min_y_intercept_5m'][end_indice]
    print(max_slope, max_y_intercept, min_slope, min_y_intercept)
    end_indice_sp_res = df_5m[df_5m['date'] == entry_time].index[0]
    
    # Calculate x values for trendlines
    x_values = list(range(end_indice - number_candles_to_draw, end_indice + 1))
    x_values_date_time = df_5m.loc[x_values, 'date']
    
    # Calculate y values for trendlines
    y_values_max = [max_slope * x + max_y_intercept for x in x_values]
    y_values_min = [min_slope * x + min_y_intercept for x in x_values]

    # Add trendlines to the figure
    fig.add_trace(go.Scatter(x=x_values_date_time, y=y_values_max, mode='lines', name="Max Trendline", marker=dict(color='blue', size=7)))
    fig.add_trace(go.Scatter(x=x_values_date_time, y=y_values_min, mode='lines', name="Min Trendline", marker=dict(color='blue', size=7)))


    """
    - Vẽ kc và ht 1h lên data khung 5m
    """
    """
    length = 570
    for i in range(len(df_5m)):
        if (df_5m['support_1h_1h'][i] != None):
            x = np.arange(i - length, i + 1, 1)
            time_range = df_5m.loc[x, 'date']
            fig.add_trace(go.Scatter(
                x=time_range,
                y=np.full([1, length * 2], df_5m['support_1h_1h'][i])[0],
                marker=dict(color='green', size=7),
                mode='lines',
                name='support_1h',
            ))

    for i in range(len(df_5m)):
        if (df_5m['resistance_1h_1h'][i] != None):
            x = np.arange(i + 1 - length, i + 1, 1)
            time_range = df_5m.loc[x, 'date']
            fig.add_trace(go.Scatter(
                x=time_range,
                y=np.full([1, length * 2], df_5m['resistance_1h_1h'][i])[0],
                marker=dict(color='red', size=7),
                mode='lines',
                name='resistance_1h',
            ))
    """

    """
    - Support & Resistance, peak & bottom gần nhất của cây nến vào lệnh
    """
    length = 500
    # resistance = df_5m['previous_nearest_resistance_1h'][end_indice_sp_res]
    # support = df_5m['previous_nearest_support_1h'][end_indice_sp_res]
    # bottom = df_5m['previous_nearest_bottom_5m'][end_indice_sp_res]
    # peak = df_5m['previous_nearest_peak_5m'][end_indice_sp_res]
    # print(resistance, bottom)

    # x = np.arange(end_indice_sp_res + 1 - length, end_indice_sp_res + 1, 1)
    # time_range = df_5m.loc[x, 'date']

    # fig.add_trace(go.Scatter(
    #             x=time_range,
    #             y=np.full([1, length * 2], bottom)[0],
    #             marker=dict(color='black', size=7),
    #             mode='lines',
    #             name='bottom_5m',
    #         ))

    # fig.add_trace(go.Scatter(
    #             x=time_range,
    #             y=np.full([1, length * 2], resistance)[0],
    #             marker=dict(color='brown', size=7),
    #             mode='lines',
    #             name='resistance_1h',
    #         ))
    

    # entry_indice = df_5m[df_5m['date'] == entry_time].index[0]
    # exit_indice = df_5m[df_5m['date'] == exit_time].index[0]

    # fig.add_trace(go.Scatter(
    #     x=[entry_time],
    #     y=[df_5m['open'][entry_indice]],
    #     marker=dict(color="black", size=7),
    #     mode="markers",
    #     name="entry_candle"
    # ))

    # fig.add_trace(go.Scatter(
    #     x=[exit_time],
    #     y=[df_5m['close'][exit_indice]],
    #     marker=dict(color="black", size=7),
    #     mode="markers",
    #     name="exit_candle"
    # ))
    
    # fig.add_trace(go.Scatter(
    #     x=time_range,
    #     y=df_5m['ma200_1h'],
    #     marker=dict(color="brown", size=7),
    #     mode="markers",
    #     name="200ma"
    # ))

    # Update layout
    fig.update_layout(
        title="Price action",
        xaxis_title="Date",
        yaxis_title="Value",
        showlegend=True,
        template="plotly_white"
    )

    # Show plot
    fig.show()
    
