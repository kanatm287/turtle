

def average_true_range(period, data_frame):

    data_frame["previous_day_close"] = data_frame["close"].shift(1).fillna(method="backfill")

    data_frame["true_range_one"] = data_frame["high"] - data_frame["low"]
    data_frame["true_range_second"] = data_frame["high"] - data_frame["previous_day_close"]
    data_frame["true_range_third"] = data_frame["previous_day_close"] - data_frame["low"]

    data_frame["true_range"] = data_frame[["true_range_one", "true_range_second", "true_range_third"]].max(axis=1)

    data_frame["average_true_range"] = data_frame["true_range"].ewm(span=period, adjust=False).mean()

    return data_frame


def dollar_volatility(data_frame):

    data_frame["dollar_volatility"] = data_frame["close"] * data_frame["average_true_range"]

    return data_frame


def high_low(data_frame, period):

    data_frame["average_high"] = data_frame["high"].rolling(window=period).mean().fillna(method="backfill")

    data_frame["average_low"] = data_frame["low"].rolling(window=period).mean().fillna(method="backfill")

    return data_frame


def prepare(data_frame, average_true_range_period, high_low_period):

    data_frame = average_true_range(average_true_range_period, data_frame)

    data_frame = dollar_volatility(data_frame)

    data_frame = high_low(data_frame, high_low_period)

    return data_frame
