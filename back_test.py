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

import back_test_utils as utils
import pandas as pd
import zipline
import math

import pyfolio as pf
from IPython import get_ipython
ipy = get_ipython()
if ipy is not None:
    ipy.run_line_magic('matplotlib', 'inline')

# silence warnings
import warnings
warnings.filterwarnings('ignore')


class BackTest(object):

    def __init__(self, params):
        self.symbol = params["symbol"]

        self.minute_data = params["minute_data"]
        self.range_data = params["range_data"]

        self.start_session = params["start_session"]
        self.end_session = params["end_session"]

        self.initial_portfolio_value = params["portfolio_value"]

        self.range_time_frame = params["range_time_frame"]

        self.current_high_entry = None
        self.current_low_entry = None

        self.current_high_exit = None
        self.current_low_exit = None

        self.current_average_true_range = None
        self.current_dollar_volatility = None

        self.current_unit_size = None

        self.last_trade_price = None
        self.stop_loss_price = None
        self.next_approved_trade_price = None

        self.price_change_permission = False
        self.stop_loss_permission = False

        self.short_is_active = False
        self.long_is_active = False

        self.trades_left = 4

        self.last_position_amount = 0

        self.performance = self.get_performance()

    def initialize(self, context):

        context.set_benchmark(symbol(self.symbol))

        context.set_slippage(slippage.NoSlippage())

        context.scheduled_data = {}

    def position(self, context):

        return context.portfolio.positions[symbol(self.symbol)].amount

    def trade_price(self, context):

        return context.portfolio.positions[symbol(self.symbol)].cost_basis

    def order_not_exists(self):

        return not get_open_orders(symbol(self.symbol))

    def order_exists(self):

        return get_open_orders(symbol(self.symbol))

    def set_range_params(self, params, context):

        self.current_high_entry = params.iloc[0]["high_entry"]
        self.current_low_entry = params.iloc[0]["low_entry"]

        self.current_high_exit = params.iloc[0]["high_exit"]
        self.current_low_exit = params.iloc[0]["low_exit"]

        self.current_average_true_range = params.iloc[0]["average_true_range"]
        self.current_dollar_volatility = params.iloc[0]["dollar_volatility"]

        self.current_unit_size = int(math.floor(0.01 * context.portfolio.portfolio_value /
                                                self.current_dollar_volatility))

    def set_last_range_params(self, context, current_time):

        if self.range_time_frame == "hour":
            if current_time.minute == 59:
                # print(self.range_time_frame)
                # print(current_time)
                self.set_range_params(self.range_data.loc[self.range_data["date"] == current_time], context)
            else:
                pass
        elif self.range_time_frame == "day":
            if current_time.hour == 23 and current_time.minute == 59:
                # print(self.range_time_frame)
                # print(current_time)
                self.set_range_params(self.range_data.loc[self.range_data["date"] == current_time], context)
            else:
                pass

    def calculate_position_in_percent(self, current_price, context):

        print(self.current_dollar_volatility)
        print(self.current_unit_size)

        position_in_percent = (self.last_position_amount + self.current_unit_size * current_price) / \
                              context.portfolio.portfolio_value

        print("position in percent", position_in_percent)

        self.last_position_amount = self.last_position_amount + self.current_unit_size * current_price

        print("last position amount", self.last_position_amount)

        return position_in_percent

    def initial_trade_params(self):

        self.trades_left = 4
        self.last_trade_price = None
        self.next_approved_trade_price = None
        self.stop_loss_price = None
        self.long_is_active = False
        self.short_is_active = False
        self.last_position_amount = 0

    def handle_data(self, context, data):

        current_price = data.current(symbol(self.symbol), "price")

        current_time = pd.Timestamp(get_datetime())

        self.set_last_range_params(context, current_time)

        # Open long position
        if self.order_not_exists() and self.trades_left > 0 and not self.short_is_active:
            if self.current_high_entry:
                if current_price > self.current_high_entry:
                    # print("current price", current_price, "high average", self.current_high_entry)
                    if self.trades_left == 4:
                        print("buy initial trade")
                        print("current time", current_time,
                              "current price", current_price,
                              "unit size", self.current_unit_size,
                              "current dollar volatility", self.current_dollar_volatility)
                        order_target_percent(symbol(self.symbol),
                                             self.calculate_position_in_percent(current_price, context))
                        self.trades_left = self.trades_left - 1
                        self.price_change_permission = True
                        self.stop_loss_permission = True
                        self.last_trade_price = current_price
                        self.long_is_active = True
                        self.short_is_active = False

                    elif self.stop_loss_price and self.next_approved_trade_price and \
                            self.long_is_active > 0 and current_price > self.next_approved_trade_price:
                        print("buy additional trade")
                        print("current position amount", self.position(context))
                        print("current time", current_time,
                              "current price", current_price,
                              "unit size", self.current_unit_size,
                              "current dollar volatility", self.current_dollar_volatility)
                        order_target_percent(symbol(self.symbol),
                                             self.calculate_position_in_percent(current_price, context))
                        self.trades_left = self.trades_left - 1
                        self.price_change_permission = True
                        self.last_trade_price = current_price
                        self.long_is_active = True
                        self.short_is_active = False
                    else:
                        pass

        # Open short position
        if self.order_not_exists() and self.trades_left > 0 and not self.long_is_active:
            if self.current_low_entry:
                if current_price < self.current_low_entry:
                    if self.trades_left == 4:
                        print("sell initial trade")
                        print("current time", current_time,
                              "current price", current_price,
                              "unit size", self.current_unit_size,
                              "current dollar volatility", self.current_dollar_volatility)
                        order_target_percent(symbol(self.symbol), -1 *
                                             self.calculate_position_in_percent(current_price, context))
                        self.trades_left = self.trades_left - 1
                        self.price_change_permission = True
                        self.stop_loss_permission = True
                        self.last_trade_price = current_price
                        self.long_is_active = False
                        self.short_is_active = True
                    elif self.stop_loss_price and self.next_approved_trade_price and \
                            self.short_is_active and current_price < self.next_approved_trade_price:
                        print("sell additional trade")
                        print("current position amount", self.position(context))
                        print("current time", current_time,
                              "current price", current_price,
                              "unit size", self.current_unit_size,
                              "current dollar volatility", self.current_dollar_volatility)
                        order_target_percent(symbol(self.symbol), -1 *
                                             self.calculate_position_in_percent(current_price, context))
                        self.trades_left = self.trades_left - 1
                        self.price_change_permission = True
                        self.last_trade_price = current_price
                        self.long_is_active = False
                        self.short_is_active = True
                    else:
                        pass

        # Set stop loss price,
        if self.trades_left == 3 and self.trade_price(context) and self.stop_loss_permission:
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
        if self.position(context) != 0 and self.order_not_exists():
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
        if self.position(context) != 0 and self.order_not_exists():
            if self.long_is_active and self.current_low_exit:
                if self.trade_price(context) < current_price < self.current_low_exit:
                    order_target_percent(symbol(self.symbol), 0)
                    self.initial_trade_params()
                    print("take profit, close long position")
                    print("portfolio value", context.portfolio.portfolio_value)
            elif self.short_is_active and self.current_high_exit:
                if self.trade_price(context) > current_price > self.current_high_exit:
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


symbol = "BTCUSD"

test_params = utils.initial_test_params(symbol, 4380, 20, 55, 20, 1000000, "hour")

result = BackTest(test_params).performance

# returns, positions, transactions = pf.utils.extract_rets_pos_txn_from_zipline(result)

# pf.create_full_tear_sheet(returns, positions=positions, transactions=transactions, round_trips=True)
#                           # live_start_date='2009-10-22', round_trips=True)

print(result)

import visualize_data

columns = ["algo_volatility",
           "algorithm_period_return",
           "benchmark_period_return",
           "benchmark_volatility",
           "shorts_count"]

visualize_data.algo_vs_benchmark(result, columns[1], columns[2])

result.to_csv("./" + symbol + "_result.csv", header=True)
