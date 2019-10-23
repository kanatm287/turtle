import pandas as pd
import load
import os

symbol = "BTCUSD"
days = 365

if not os.path.isfile("./" + symbol + ".csv"):

    minute_dataframe = load.exchange_historical_data(symbol, days)

    minute_dataframe = minute_dataframe.resample("1min").mean()

    minute_dataframe.fillna(method="ffill", inplace=True)

    minute_dataframe["date_string"] = minute_dataframe.index.strftime('%Y-%m-%d')

    minute_dataframe.reset_index(level=0, inplace=True)

    minute_dataframe = minute_dataframe.merge(minute_dataframe.groupby("date_string").size().to_frame("count"),
                                              on="date_string",
                                              how='inner')

    minute_dataframe = minute_dataframe.loc[minute_dataframe["count"] == 1440]

    minute_dataframe = minute_dataframe.drop(columns=["date_string", "count"])

    minute_dataframe.set_index("date", inplace=True)

    minute_dataframe.sort_index(inplace=True)

    minute_dataframe.to_csv("./" + symbol + ".csv", header=True)

else:

    minute_dataframe = pd.read_csv("./" + symbol + ".csv")

    minute_dataframe = minute_dataframe.set_index(pd.DatetimeIndex(minute_dataframe["date"]))

    minute_dataframe = minute_dataframe.drop(columns=["date"])
