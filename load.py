import pandas as pd
import functools
import bitfinex
import time

from datetime import datetime, timedelta


def request_and_generate_dataframe(params, df):

    # Define the start date
    t_start = time.mktime(params[1].timetuple()) * 1000

    # Define the end date
    t_stop = time.mktime(params[2].timetuple()) * 1000

    # This will return minute data
    time_frame = "1m"

    # We want the maximum of 1000 data points
    limit = 720

    # Create pandas data frame and clean/format data

    names = ["date", "open", "close", "high", "low", "volume"]

    api_v2 = bitfinex.bitfinex_v2.api_v2()

    response = []

    response.extend(api_v2.candles(
        symbol=params[0].lower(), interval=time_frame, limit=limit, start=t_stop, end=t_start))

    if df.size > 0:
        print("accumulated rows", df["date"].size,
              "is response empty", len(response) == 0,
              "number of rows in response", len(response))

    elif response[0] == "error":
        print(params[0], response)

    if df.empty:
        time.sleep(1.05)
        return pd.DataFrame(response, columns=names)
    elif len(response) == 0 or response[0] == "error":
        time.sleep(1.05)
        return df
    else:
        time.sleep(1.05)
        return pd.concat([df, pd.DataFrame(response, columns=names)])


def generate_date_sequence(end_date_seq):

    symbol = end_date_seq[-1][0]

    end_date = end_date_seq[-1][-1]

    return end_date_seq.append([symbol, end_date, end_date - timedelta(minutes=720)])


def exchange_historical_data(symbol, days_to_load):

    minutes_to_load = days_to_load * 24 * 60

    end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)

    date_seq = [[symbol, end_date, end_date - timedelta(minutes=720)]]

    periods = int(minutes_to_load / 720)

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


