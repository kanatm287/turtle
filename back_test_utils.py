from collections import OrderedDict
from datetime import timedelta

import pandas as pd
import pre_process
import hourly_data
import turtle_data
import math


def start_date(data_frame):

    return data_frame.reset_index().iloc[0].loc["date"].tz_localize("UTC").to_pydatetime()


def end_date(data_frame):

    return data_frame.reset_index().iloc[-1].loc["date"].tz_localize("UTC").to_pydatetime()


def generate_minute_test_data(symbol, data_frame):

    data = OrderedDict()

    data[symbol] = data_frame

    data[symbol] = data[symbol][["open", "high", "low", "close", "volume"]]

    panel = pd.Panel(data)
    panel.minor_axis = ["open", "high", "low", "close", "volume"]

    return panel


def initial_test_params(symbol,
                        days_to_load,
                        average_true_range_period,
                        entry_high_low_period,
                        exit_high_low_period,
                        initial_balance):

    minute_data_frame = pre_process.minute_data(symbol, days_to_load)

    hour_data_frame = turtle_data.prepare(hourly_data.generate(minute_data_frame),
                                          average_true_range_period,
                                          entry_high_low_period,
                                          exit_high_low_period)

    return {"symbol": symbol,
            "portfolio_value": initial_balance,
            "minute_data": generate_minute_test_data(symbol, minute_data_frame),
            "hour_data": hour_data_frame,
            "start_session": start_date(minute_data_frame) + timedelta(days=int(math.ceil(entry_high_low_period/24))),
            "end_session": end_date(minute_data_frame)}
