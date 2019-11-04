from collections import OrderedDict
from datetime import timedelta

import pandas as pd
import pre_process
import hourly_data
import turtle_data
import daily_data
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


def generate_multi_asset_minute_test_data(symbol, data_frame, test_minute_data):

    test_minute_data[symbol] = data_frame

    test_minute_data[symbol] = test_minute_data[symbol][["open", "high", "low", "close", "volume"]]

    return test_minute_data


def initial_test_params(symbol,
                        days_to_load,
                        average_true_range_period,
                        entry_high_low_period,
                        exit_high_low_period,
                        initial_balance,
                        range_time_frame):

    minute_data_frame = pre_process.minute_data(symbol, days_to_load)

    range_data_frame = None

    time_delta = None

    if range_time_frame == "hour":
        time_delta = timedelta(hours=entry_high_low_period)
        range_data_frame = turtle_data.prepare(hourly_data.generate(minute_data_frame),
                                               average_true_range_period,
                                               entry_high_low_period,
                                               exit_high_low_period)
    elif range_time_frame == "day":
        time_delta = timedelta(days=entry_high_low_period)
        range_data_frame = turtle_data.prepare(daily_data.generate(minute_data_frame),
                                               average_true_range_period,
                                               entry_high_low_period,
                                               exit_high_low_period)

    return {"symbol": symbol,
            "portfolio_value": initial_balance,
            "minute_data": generate_minute_test_data(symbol, minute_data_frame),
            "range_data": range_data_frame,
            "start_session": start_date(minute_data_frame) + time_delta,
            "end_session": end_date(minute_data_frame),
            "range_time_frame": range_time_frame}


def multi_asset_initial_test_params(symbols,
                                    days_to_load,
                                    average_true_range_period,
                                    entry_high_low_period,
                                    exit_high_low_period,
                                    initial_balance,
                                    range_time_frame):

    test_minute_data = OrderedDict()

    range_data_frame = {}

    start_session = None

    end_session = None

    time_delta = None

    for symbol in symbols:

        minute_data_frame = pre_process.minute_data(symbol, days_to_load)

        symbol_start_session = start_date(minute_data_frame)

        symbol_end_session = end_date(minute_data_frame)

        if not start_session:

            start_session = symbol_start_session
            end_session = symbol_end_session

        elif start_session > symbol_end_session:

            start_session = symbol_end_session

        test_minute_data = generate_multi_asset_minute_test_data(symbol, minute_data_frame, test_minute_data)

        if range_time_frame == "hour":
            time_delta = timedelta(hours=entry_high_low_period)
            range_data_frame[symbol] = turtle_data.prepare(hourly_data.generate(minute_data_frame),
                                                           average_true_range_period,
                                                           entry_high_low_period,
                                                           exit_high_low_period)
        elif range_time_frame == "day":
            time_delta = timedelta(days=entry_high_low_period)
            range_data_frame[symbol] = turtle_data.prepare(daily_data.generate(minute_data_frame),
                                                           average_true_range_period,
                                                           entry_high_low_period,
                                                           exit_high_low_period)

    panel = pd.Panel(test_minute_data)
    panel.minor_axis = ["open", "high", "low", "close", "volume"]

    return {"symbols": symbols,
            "portfolio_value": initial_balance,
            "minute_data": panel,
            "range_data": range_data_frame,
            "start_session": start_session + time_delta,
            "end_session": end_session,
            "range_time_frame": range_time_frame}
