# Load the Pandas libraries with alias "pd"
import pandas as pd
import bitfinex

# Load OrederedDict from collections
from datetime import datetime, timedelta, timezone
from collections import OrderedDict
from time import mktime


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

    return end_date_seq.append([symbol, end_date, end_date - timedelta(minutes=600)])


def request_and_generate_dataframe(params, df):

    # Set step size
    time_step = 60000000

    # Define the start date
    t_start = time.mktime(params[1].timetuple()) * 1000

    # Define the end date
    t_stop = time.mktime(params[2].timetuple()) * 1000

    # This will return minute data
    time_frame = "1m"

    # We want the maximum of 1000 data points
    limit = 1000

    # Create pandas data frame and clean/format data

    names = ["date", "open", "close", "high", "low", "volume"]

    df = pd.DataFrame(request_data(start=t_start, stop=t_stop, symbol=symbol.lower(),
                                   interval=time_frame, tick_limit=limit,
                                   step=time_step),
                      columns=names)

    df.drop_duplicates(inplace=True)

    df["date"] = pd.to_datetime(df["date"], unit="ms")

    df.set_index("date", inplace=True)

    df.sort_index(inplace=True)

    return df


print(exchange_historical_data("BTCUSD"))
