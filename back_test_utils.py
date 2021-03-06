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


def multi_asset_with_cross_initial_test_params(params):

    test_minute_data = OrderedDict()

    range_data_frame = {}

    start_session = None

    end_session = None

    time_delta = None

    for symbol in params["symbols"]:

        if symbol in params["cross_symbols"]:
            minute_data_frame = pre_process.synthetic_minute_data(params["cross_symbols"][symbol]["long"],
                                                                  params["cross_symbols"][symbol]["short"],
                                                                  params["data_source"])
        else:
            minute_data_frame = pre_process.minute_data(symbol,
                                                        params["days_to_load"],
                                                        params["data_source"])

        symbol_start_session = start_date(minute_data_frame)

        symbol_end_session = end_date(minute_data_frame)

        if not start_session:
            start_session = symbol_start_session
        elif start_session < symbol_start_session:
            start_session = symbol_start_session

        if not end_session:
            end_session = symbol_end_session
        elif end_session > symbol_end_session:
            end_session = symbol_end_session

        test_minute_data = generate_multi_asset_minute_test_data(symbol, minute_data_frame, test_minute_data)

        if params["time_frame"] == "hour":
            time_delta = timedelta(hours=params["entry_period"])
            range_data_frame[symbol] = turtle_data.prepare(hourly_data.generate(minute_data_frame),
                                                           params["average_true_range_period"],
                                                           params["entry_period"],
                                                           params["exit_period"])
        elif params["time_frame"] == "day":
            time_delta = timedelta(days=params["entry_period"])
            range_data_frame[symbol] = turtle_data.prepare(daily_data.generate(minute_data_frame),
                                                           params["average_true_range_period"],
                                                           params["entry_period"],
                                                           params["exit_period"])

        print(symbol, start_session, end_session)

    panel = pd.Panel(test_minute_data)
    panel.minor_axis = ["open", "high", "low", "close", "volume"]

    return {"symbols": params["symbols"],
            "cross_symbols": params["cross_symbols"],
            "forbidden_symbols": params["forbidden_symbols"],
            "portfolio_value": params["initial_balance"],
            "minute_data": panel,
            "range_data": range_data_frame,
            "start_session": start_session,
            "end_session": end_session,
            "range_time_frame": params["time_frame"],
            "days_to_trade": params["days_to_trade"],
            "start_timedelta": time_delta,
            "benchmark_symbol": params["benchmark_symbol"]}
