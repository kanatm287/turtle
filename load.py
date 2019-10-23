# Load the Pandas libraries with alias "pd"
import pandas as pd
import functools
import bitfinex
import time
import sys

# Load OrederedDict from collections
from datetime import datetime, timedelta, timezone
from collections import OrderedDict


def request_data(start, stop, symbol, interval, tick_limit, step):

    # Create api instance
    api_v2 = bitfinex.bitfinex_v2.api_v2()

    data = []

    start = start - step

    while start < stop:
        start = start + step

    end = start + step

    res = api_v2.candles(symbol=symbol, interval=interval, limit = tick_limit, start = start, end = end)
    data.extend(res)
    return data


def generate_date_sequence(end_date_seq):

    symbol = end_date_seq[-1][0]

    end_date = end_date_seq[-1][-1]

    return end_date_seq.append([symbol, end_date, end_date - timedelta(minutes=600), end_date - timedelta(minutes=660)])


def request_and_generate_dataframe(params, df):

    # print(params)

    # Set step size
    time_step = 60000000

    # Define the start date
    t_start = time.mktime(params[1].timetuple()) * 1000

    # Define the end date
    t_stop = time.mktime(params[2].timetuple()) * 1000

    # This will return minute data
    time_frame = "1m"

    # We want the maximum of 1000 data points
    limit = 660

    # Create pandas data frame and clean/format data

    names = ["date", "open", "close", "high", "low", "volume"]

    new_df = pd.DataFrame(request_data(start=t_start, stop=t_stop, symbol=params[0].lower(),
                                       interval=time_frame, tick_limit=limit,
                                       step=time_step),
                          columns=names)

    if df.empty:
        time.sleep(1)
        return new_df
    else:
        time.sleep(1)
        return pd.concat([df, new_df])


def exchange_historical_data(symbol, days_to_load):

    minutes_to_load = days_to_load * 24 * 60

    end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    date_seq = [[symbol, end_date, end_date - timedelta(minutes=600)]]

    periods = int(minutes_to_load / 600)

    while periods > 0:

        generate_date_sequence(date_seq)

        periods -= 1

    df = functools.reduce(lambda a, b: request_and_generate_dataframe(b, a),
                          date_seq,
                          pd.DataFrame())

    df.drop_duplicates(inplace=True)

    df["date"] = pd.to_datetime(df["date"], unit="ms")

    df.set_index("date", inplace=True)

    df.sort_index(inplace=True)

    return df


