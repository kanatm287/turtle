from functools import reduce
import pandas as pd


def generate(data_frame):

    data_frame["date_string"] = data_frame.index.strftime("%Y-%m-%d")

    daily_data_open = data_frame.groupby("date_string").first().reset_index()[["date_string", "open"]]

    daily_data_high = data_frame.groupby("date_string").max().reset_index()[["date_string", "high"]]

    daily_data_low = data_frame.groupby("date_string").min().reset_index()[["date_string", "low"]]

    daily_data_close = data_frame.groupby("date_string").last().reset_index()[["date_string", "close"]]

    daily_data_volume = data_frame.groupby("date_string").sum().reset_index()[["date_string", "volume"]]

    data_frames = [data_frame.reset_index().drop(columns=["open", "high", "low", "close", "volume"]),
                   daily_data_open,
                   daily_data_high,
                   daily_data_low,
                   daily_data_close,
                   daily_data_volume]

    daily_data = reduce(lambda left, right: pd.merge(left, right, on="date_string"), data_frames)

    daily_data.set_index("date", inplace=True)

    daily_data.sort_index(inplace=True)

    daily_data = daily_data[daily_data.index.hour == 23]

    return daily_data[daily_data.index.minute == 59].drop(columns=["date_string"])
