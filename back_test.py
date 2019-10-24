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
        if self.order_not_exists() and self.trades_left > 0 and not self.short_is_active:
            if self.current_high_average_entry:
                if current_price > self.current_high_average_entry:
                    if self.trades_left == 4:
                        print("buy initial trade")
                        print("current time", current_time, "current price", current_price)
                        order_target_percent(symbol(self.symbol), self.current_unit_size)
                        self.trades_left = self.trades_left - 1
                        self.price_change_permission = True
                        self.stop_loss_permission = True
                        self.last_trade_price = current_price
                        self.long_is_active = True
                        self.short_is_active = False

                    elif self.next_approved_trade_price and \
                            self.long_is_active > 0 and current_price > self.next_approved_trade_price:
                        print("sell additional trade")
                        print("current time", current_time, "current price", current_price)
                        order_target_percent(symbol(self.symbol), (5 - self.trades_left) * self.current_unit_size)
                        self.trades_left = self.trades_left - 1
                        self.price_change_permission = True
                        self.last_trade_price = current_price
                        self.long_is_active = True
                        self.short_is_active = False
                    else:
                        pass

        # Open short position
        if self.order_not_exists() and self.trades_left > 0 and not self.long_is_active:
            if self.current_low_average_entry:
                if current_price < self.current_low_average_entry:
                    if self.trades_left == 4:
                        print("sell initial trade")
                        print("current time", current_time, "current price", current_price)
                        order_target_percent(symbol(self.symbol), -1 * self.current_unit_size)
                        self.trades_left = self.trades_left - 1
                        self.price_change_permission = True
                        self.stop_loss_permission = True
                        self.last_trade_price = current_price
                        self.long_is_active = False
                        self.short_is_active = True
                    elif self.next_approved_trade_price and \
                            self.short_is_active and current_price < self.next_approved_trade_price:
                        print("sell additional trade")
                        print("current time", current_time, "current price", current_price)
                        order_target_percent(symbol(self.symbol), -(5 - self.trades_left) * self.current_unit_size)
                        print("position", context.portfolio.positions[symbol(self.symbol)])
                        self.trades_left = self.trades_left - 1
                        self.price_change_permission = True
                        self.last_trade_price = current_price
                        self.long_is_active = False
                        self.short_is_active = True
                    else:
                        pass

        # Set stop loss price,
        if self.order_not_exists() and self.stop_loss_permission:
            print("last traded price", self.trade_price(context))
            if self.long_is_active:
                self.stop_loss_price = self.trade_price(context) - (2 * self.current_average_true_range)
                print("set stop loss for long", self.stop_loss_price)
                self.stop_loss_permission = False
            elif self.short_is_active:
                self.stop_loss_price = self.trade_price(context) + (2 * self.current_average_true_range)
                print("set stop loss for short", self.stop_loss_price)
                self.stop_loss_permission = False
            print("position", self.position(context))

        # Calculate next approved trade price
        if self.last_trade_price and self.price_change_permission:
            if self.long_is_active:
                if self.trades_left == 4:
                    self.next_approved_trade_price = self.trade_price(context) + self.current_average_true_range / 2
                else:
                    self.next_approved_trade_price = self.last_trade_price + self.current_average_true_range / 2
                self.price_change_permission = False
                print("set trade params")
                print("current time", current_time, "current price", current_price)
                print("trades left", self.trades_left)
                print("ATR/2", self.current_average_true_range / 2,
                      "next approved price", self.next_approved_trade_price)

            elif self.short_is_active:
                if self.trades_left == 4:
                    self.next_approved_trade_price = self.trade_price(context) - self.current_average_true_range / 2
                else:
                    self.next_approved_trade_price = self.last_trade_price - self.current_average_true_range / 2
                self.price_change_permission = False
                print("set trade params")
                print("current time", current_time, "current price", current_price, "last price", self.last_trade_price)
                print("trades left", self.trades_left)
                print("ATR/2", self.current_average_true_range / 2,
                      "next approved price", self.next_approved_trade_price)

        # Stop Loss
        if self.position_exists(context) and self.order_not_exists():
            if self.long_is_active:
                if current_price < self.stop_loss_price:
                    order_target_percent(symbol(self.symbol), 0)
                    print("stop loss, close long position")
                    print("current time", current_time, "current price", current_price)
                    print("stop loss price", self.stop_loss_price)
                    print("portfolio value", context.portfolio.portfolio_value)
                    self.initial_trade_params()
            elif self.short_is_active:
                if current_price > self.stop_loss_price:
                    order_target_percent(symbol(self.symbol), 0)
                    print("stop loss, close short position")
                    print("current time", current_time, "current price", current_price)
                    print("stop loss price", self.stop_loss_price)
                    print("portfolio value", context.portfolio.portfolio_value)
                    self.initial_trade_params()

        # Take profit
        if self.position_exists(context) and self.order_not_exists():
            if self.long_is_active and self.current_low_average_exit:
                if self.trade_price(context) < current_price < self.current_low_average_exit:
                    order_target_percent(symbol(self.symbol), 0)
                    self.initial_trade_params()
                    print("take profit, close long position")
                    print("portfolio value", context.portfolio.portfolio_value)
            elif self.short_is_active and self.current_high_average_exit:
                if self.trade_price(context) > current_price > self.current_high_average_exit:
                    order_target_percent(symbol(self.symbol), 0)
                    self.initial_trade_params()
                    print("take profit, close short position")
                    print("portfolio value", context.portfolio.portfolio_value)

    def get_performance(self):

        return zipline.run_algorithm(start=self.start_session,
                                     end=self.end_session,
                                     initialize=self.initialize,
                                     trading_calendar=always_open.AlwaysOpenCalendar(),
                                     capital_base=self.initial_portfolio_value,
                                     handle_data=self.handle_data,
                                     data_frequency="minute",
                                     data=self.minute_data)


result = BackTest(utils.initial_test_params("BTCUSD", 365, 20, 55, 20, 1000000)).performance

print(result)
