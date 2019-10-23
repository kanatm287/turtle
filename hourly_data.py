from functools import reduce
import pandas as pd


def generate(data_frame):

    data_frame["date_hour_string"] = data_frame.index.strftime("%Y-%m-%d-%H")

    hourly_data_open = data_frame.groupby("date_hour_string").first().reset_index()[["date_hour_string", "open"]]

    hourly_data_high = data_frame.groupby("date_hour_string").max().reset_index()[["date_hour_string", "high"]]

    hourly_data_low = data_frame.groupby("date_hour_string").min().reset_index()[["date_hour_string", "low"]]

    hourly_data_close = data_frame.groupby("date_hour_string").last().reset_index()[["date_hour_string", "close"]]

    hourly_data_volume = data_frame.groupby("date_hour_string").sum().reset_index()[["date_hour_string", "volume"]]

    data_frames = [data_frame.reset_index().drop(columns=["open", "high", "low", "close", "volume"]),
                   hourly_data_open,
                   hourly_data_high,
                   hourly_data_low,
                   hourly_data_close,
                   hourly_data_volume]

    hourly_data = reduce(lambda left, right: pd.merge(left, right, on="date_hour_string"), data_frames)

    hourly_data.set_index("date", inplace=True)

    hourly_data.sort_index(inplace=True)

    return hourly_data[hourly_data.index.minute == 59].drop(columns=["date_hour_string"])
