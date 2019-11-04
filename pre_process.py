import pandas as pd
import load
import os


def minute_data(symbol, days):

    if not os.path.isfile("./" + symbol + ".csv"):

        minute_dataframe = load.exchange_historical_data(symbol, days)

        minute_dataframe = minute_dataframe.resample("1min").mean()

        minute_dataframe.fillna(method="ffill", inplace=True)

        minute_dataframe["date_string"] = minute_dataframe.index.strftime('%Y-%m-%d')

        minute_dataframe.reset_index(level=0, inplace=True)

        minute_dataframe = minute_dataframe.merge(minute_dataframe
                                                  .groupby("date_string")
                                                  .size()
                                                  .to_frame("count")
                                                  .reset_index(),
                                                  on="date_string",
                                                  how='inner')

        minute_dataframe = minute_dataframe.loc[minute_dataframe["count"] == 1440]

        minute_dataframe = minute_dataframe.drop(columns=["date_string", "count"])

        minute_dataframe.set_index("date", inplace=True)

        minute_dataframe.sort_index(inplace=True)

        minute_dataframe.to_csv("./" + symbol + ".csv", header=True)

        return minute_dataframe

    else:

        minute_dataframe = pd.read_csv("./" + symbol + ".csv")

        minute_dataframe = minute_dataframe.set_index(pd.DatetimeIndex(minute_dataframe["date"]))

        return minute_dataframe.drop(columns=["date"])


def rename_columns(data_frame, symbol):

    return data_frame.rename(columns={"open": symbol + "_open",
                                      "high": symbol + "_high",
                                      "low": symbol + "_low",
                                      "close": symbol + "_close",
                                      "volume": symbol + "_volume"})[["date",
                                                                     symbol + "_open",
                                                                     symbol + "_high",
                                                                     symbol + "_low",
                                                                     symbol + "_close",
                                                                     symbol + "_volume"]]


def synthetic_minute_data(long_param, short_param):

    long_dataframe = rename_columns(pd.read_csv("./" + long_param + ".csv"), long_param)
    short_dataframe = rename_columns(pd.read_csv("./" + short_param + ".csv"), short_param)

    combined_dataframe = pd.merge(long_dataframe, short_dataframe, on="date")

    combined_dataframe["open"] = combined_dataframe[long_param + "_open"] / combined_dataframe[short_param + "_open"]
    combined_dataframe["high"] = combined_dataframe[long_param + "_high"] / combined_dataframe[short_param + "_high"]
    combined_dataframe["low"] = combined_dataframe[long_param + "_low"] / combined_dataframe[short_param + "_low"]
    combined_dataframe["close"] = combined_dataframe[long_param + "_close"] / combined_dataframe[short_param + "_close"]
    combined_dataframe["volume"] = \
        combined_dataframe[long_param + "_volume"] / combined_dataframe[short_param + "_volume"]

    combined_dataframe = combined_dataframe.set_index(pd.DatetimeIndex(combined_dataframe["date"]))

    # pd.set_option("display.precision", 20)

    # print(combined_dataframe)

    return combined_dataframe[["open", "high", "low", "close", "volume"]]
