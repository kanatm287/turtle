from collections import OrderedDict
from pandas import Timedelta
from datetime import datetime

import pandas as pd
import pre_process
import hourly_data
import turtle_data
import math
import pytz


def start_date(data_frame):

    return data_frame.index[0]


def end_date(data_frame):

    return data_frame.index[-1]


def generate_minute_test_data(symbol, data_frame):

    data = OrderedDict()

    # data_frame = data_frame.reset_index()
    #
    # pd.DatetimeIndex(data_frame["date"]).asi8
    #
    # print(data_frame.dtypes)

    data[symbol] = data_frame

    data[symbol] = data[symbol][["open", "high", "low", "close", "volume"]]

    panel = pd.Panel(data)
    panel.minor_axis = ["open", "high", "low", "close", "volume"]
    panel.major_axis = panel.major_axis.tz_localize(pytz.utc)

    # panel.major_axis = panel.major_axis.tz_convert(None)

    return panel


def initial_test_params(symbol, days_to_load, average_true_range_period, high_low_period):

    minute_data_frame = pre_process.minute_data(symbol, days_to_load)

    hour_data_frame = turtle_data.prepare(hourly_data.generate(minute_data_frame),
                                          average_true_range_period,
                                          high_low_period)

    return {"symbol": symbol,
            "minute_data": generate_minute_test_data(symbol, minute_data_frame),
            "hour_data": hour_data_frame,
            "start_session": (start_date(minute_data_frame) +
                              Timedelta(days=int(math.ceil(high_low_period/24)))).to_pydatetime(),
            "end_session": end_date(minute_data_frame).to_pydatetime()}
