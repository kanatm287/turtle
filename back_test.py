from zipline.api import \
    schedule_function, \
    get_open_orders, \
    order_target_percent, \
    order, \
    get_datetime, \
    symbol, \
    date_rules, \
    time_rules, \
    record, \
    set_slippage

from zipline.finance import slippage
from trading_calendars import always_open
from multiprocessing import Pool
from datetime import datetime
from pandas import Timedelta

import back_test_utils as utils
import pandas as pd
import numpy as np
import zipline
import sys
import os
import pytz


# symbol = sys.argv[1]
# average_true_range_period = sys.argv[2]
# high_low_period = sys.argv[3]


class BackTest(object):

    def __init__(self, params):
        self.symbol = params["symbol"]

        self.minute_data = params["minute_data"]

        self.hourly_data = params["hour_data"]

        self.start_session = params["start_session"]

        self.end_session = params["end_session"]

        self.initial_portfolio_value = params["portfolio_value"]

        self.current_portfolio_value = self.initial_portfolio_value

        self.current_high_average = None

        self.current_low_average = None

        self.current_average_true_range = None

        self.current_dollar_volatility = None

        self.current_unit_size = None

        self.performance = self.get_performance()

    def initialize(self, context):

        context.set_benchmark(symbol(self.symbol))

        context.set_slippage(slippage.NoSlippage())

        context.scheduled_data = {}

    def position_not_exists(self, context):

        if context.portfolio.positions[symbol(self.symbol)].amount == 0:
            return True
        else:
            return False

    def position_exists(self, context):

        if context.portfolio.positions[symbol(self.symbol)].amount != 0:
            return True
        else:
            return False

    def position(self, context):

        return context.portfolio.positions[symbol(self.symbol)].amount

    def trade_price(self, context):

        return context.portfolio.positions[symbol(self.symbol)].cost_basis

    def order_not_exists(self):

        if not get_open_orders(symbol(self.symbol)):
            return True
        else:
            return False

    def order_exists(self):

        if get_open_orders(symbol(self.symbol)):
            return True
        else:
            return False

    def set_last_hour_params(self, context, current_time):

        if current_time.minute == 59:

            params = self.hourly_data.loc[self.hourly_data["date"] == current_time]

            self.current_high_average = params.iloc[0]["average_high"]
            self.current_low_average = params.iloc[0]["average_low"]
            self.current_average_true_range = params.iloc[0]["average_true_range"]
            self.current_dollar_volatility = params.iloc[0]["dollar_volatility"]

            self.current_portfolio_value = context.portfolio.portfolio_value

            self.current_unit_size = 0.01 * self.current_portfolio_value / self.current_dollar_volatility

    def set_trades_count(self, context):

        return None

        # if context.stop_trades <= self.max_trades_per_day[0]:
        #     self.stop_trades = True
        # else:
        #     self.stop_trades = False
        #
        # if context.limit_trades <= self.max_trades_per_day[1]:
        #     self.limit_trades = True
        # else:
        #     self.limit_trades = False

    def check_and_trade(self, context, current_price, current_time, data):

        return None

    def handle_data(self, context, data):

        current_price = data.current(symbol(self.symbol), "price")

        current_time = pd.Timestamp(get_datetime())

        self.set_last_hour_params(context, current_time)

        # Open long position
        if self.current_high_average:
            if current_price > self.current_high_average:
                print("buy")
                print("portfolio value", self.current_portfolio_value)
                print("dollar volatility", self.current_dollar_volatility)
                print("ATR", self.current_average_true_range)
                print("price", current_price)
                print("unit", self.current_unit_size)
                order_target_percent(symbol(self.symbol), self.current_unit_size)

        # Open short position
        if self.current_low_average:
            if current_price < self.current_low_average:
                print("sell")
                print("portfolio value", self.current_portfolio_value)
                print("dollar volatility", self.current_dollar_volatility)
                print("ATR", self.current_average_true_range)
                print("price", current_price)
                print("unit", self.current_unit_size)
                order_target_percent(symbol(self.symbol), -1 * self.current_unit_size)

    def get_performance(self):

        performance = zipline.run_algorithm(start=self.start_session,
                                            end=self.end_session,
                                            initialize=self.initialize,
                                            trading_calendar=always_open.AlwaysOpenCalendar(),
                                            capital_base=self.initial_portfolio_value,
                                            handle_data=self.handle_data,
                                            data_frequency="minute",
                                            data=self.minute_data)

        algo_period_return = performance.algorithm_period_return[-1]
        max_drawdown = performance.max_drawdown[-1] if performance.max_drawdown[-1] != 0 else 0.0001

        return {"symbol": self.symbol,
                "start_session": self.start_session,
                "end_session": self.end_session,
                "algorithm_period_return": round(algo_period_return, 4),
                "portfolio_value": performance.portfolio_value[-1],
                "max_drawdown": round(max_drawdown, 4),
                "profit_factor": algo_period_return / abs(max_drawdown),
                "data_frame": performance}


result = BackTest(utils.initial_test_params("BTCUSD", 365, 20, 55, 1000000)).performance

print(result)
