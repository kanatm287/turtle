import plotly.graph_objects as go
import turtle_data
import hourly_data
import pre_process


def line_chart(data_frame, columns):

    fig = go.Figure()

    for column in columns:

        fig.add_trace(go.Scatter(x=data_frame.index,
                                 y=data_frame[column["column"]],
                                 name=column["column"],
                                 line_color=column["color"],
                                 opacity=0.8))

    fig.update_layout(title_text="Chart")
    fig.show()


def candle_sticks(data_frame):

    fig = go.Figure(data=[go.Candlestick(x=data_frame["date"],
                                         open=data_frame["open"],
                                         high=data_frame["high"],
                                         low=data_frame["low"],
                                         close=data_frame["close"])])

    fig.show()


hour_data_frame = turtle_data.prepare(hourly_data.generate(pre_process.minute_data("BTCUSD", 55)), 20, 55, 20)

# candle_sticks(hour_data_frame)

# columns = ["close",
#            "average_true_range",
#            "dollar_volatility",
#            "average_high_entry",
#            "average_low_entry",
#            "average_high_exit",
#            "average_low_exit"]

hour_data_frame = hour_data_frame.set_index("date")

line_chart(hour_data_frame.head(1000),
           [{"color": "red", "column": "close"},
            {"color": "green", "column": "average_high_entry"},
            {"color": "blue", "column": "average_low_entry"}])#,
            # {"color": "brown", "column": "average_high_exit"},
            # {"color": "black", "column": "average_low_exit"}])
