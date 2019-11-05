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

from trading_calendars import always_open
from zipline.finance import slippage
from datetime import timedelta

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
        self.symbols = params["symbols"]

        self.cross_symbols = params["cross_symbols"]

        self.forbidden_symbols = params["forbidden_symbols"]

        self.minute_data = params["minute_data"]
        self.range_data = params["range_data"]

        self.start_session = params["start_session"]
        self.end_session = params["end_session"]

        self.initial_portfolio_value = params["portfolio_value"]

        self.range_time_frame = params["range_time_frame"]

        self.current_high_entry = {}
        self.current_low_entry = {}

        self.current_high_exit = {}
        self.current_low_exit = {}

        self.current_average_true_range = {}
        self.current_dollar_volatility = {}

        self.current_unit_size = {}

        self.last_trade_price = {}
        self.stop_loss_price = {}
        self.next_approved_trade_price = {}

        self.price_change_permission = {}
        self.stop_loss_permission = {}

        self.short_is_active = {}
        self.long_is_active = {}

        self.trades_left = {}

        self.last_position_amount = {}

        self.cross_symbols_positions = {}

        self.set_initial_params()

        self.performance = self.get_performance()

    def set_initial_params(self):

        for current_symbol in self.symbols:

            self.current_high_entry[current_symbol] = None
            self.current_low_entry[current_symbol] = None

            self.current_high_exit[current_symbol] = None
            self.current_low_exit[current_symbol] = None

            self.current_average_true_range[current_symbol] = None
            self.current_dollar_volatility[current_symbol] = None

            self.current_unit_size[current_symbol] = None

            self.last_trade_price[current_symbol] = None
            self.stop_loss_price[current_symbol] = None
            self.next_approved_trade_price[current_symbol] = None

            self.price_change_permission[current_symbol] = False
            self.stop_loss_permission[current_symbol] = False

            self.short_is_active[current_symbol] = False
            self.long_is_active[current_symbol] = False

            self.trades_left[current_symbol] = 4

            if self.is_cross_symbol(current_symbol):

                self.cross_symbols_positions[current_symbol] = {}
                self.cross_symbols_positions[current_symbol]["long"] = 0
                self.cross_symbols_positions[current_symbol]["short"] = 0

            else:
                self.last_position_amount[current_symbol] = 0

    def initialize(self, context):

        context.set_benchmark(symbol("BTCUSD"))

        context.set_slippage(slippage.NoSlippage())

        context.scheduled_data = {}

    def position(self, context, current_symbol):

        if current_symbol in self.cross_symbols:
            return self.cross_symbols_positions[current_symbol]["long"]
        else:
            return context.portfolio.positions[symbol(current_symbol)].amount

    def trade_price(self, context, current_symbol):

        if current_symbol in self.cross_symbols:
            return self.last_trade_price[current_symbol]
        else:
            return context.portfolio.positions[symbol(current_symbol)].cost_basis

    def order_not_exists(self, current_symbol):

        return not get_open_orders(symbol(current_symbol))

    def order_exists(self, current_symbol):

        return get_open_orders(symbol(current_symbol))

    def is_cross_symbol(self, current_symbol):

        return current_symbol in self.cross_symbols

    def open_cross_symbol_position(self, action, current_symbol):

        long_base = self.cross_symbols[current_symbol]["long"]

        short_base = self.cross_symbols[current_symbol]["short"]

        self.cross_symbols_positions[current_symbol]["long"] = \
            self.cross_symbols_positions[current_symbol]["long"] + self.current_unit_size[long_base]

        self.cross_symbols_positions[current_symbol]["short"] = \
            self.cross_symbols_positions[current_symbol]["short"] + self.current_unit_size[short_base]

        print("cross symbol long open position", long_base, " amount", self.current_unit_size[long_base])
        print("cross symbol short open position", short_base, " amount", self.current_unit_size[short_base])

        if action == "buy":
            order(symbol(long_base), self.current_unit_size[long_base])
            order(symbol(short_base), -1 * self.current_unit_size[short_base])
        else:
            order(symbol(long_base), -1 * self.current_unit_size[long_base])
            order(symbol(short_base), self.current_unit_size[short_base])

    def close_cross_symbol_position(self, action, current_symbol):

        long_base = self.cross_symbols[current_symbol]["long"]

        short_base = self.cross_symbols[current_symbol]["short"]

        print("cross symbol long close position", long_base, " amount", self.current_unit_size[long_base])
        print("cross symbol short close position", short_base, " amount", self.current_unit_size[short_base])

        if action == "buy":
            order(symbol(long_base), -1 * self.current_unit_size[long_base])
            order(symbol(short_base), self.current_unit_size[short_base])

        else:
            order(symbol(long_base), self.current_unit_size[long_base])
            order(symbol(short_base), -1 * self.current_unit_size[short_base])

    def set_range_params(self, params, context, current_symbol):

        if params.size > 0:

            self.current_high_entry[current_symbol] = params.iloc[0]["high_entry"]
            self.current_low_entry[current_symbol] = params.iloc[0]["low_entry"]

            self.current_high_exit[current_symbol] = params.iloc[0]["high_exit"]
            self.current_low_exit[current_symbol] = params.iloc[0]["low_exit"]

            self.current_average_true_range[current_symbol] = params.iloc[0]["average_true_range"]
            self.current_dollar_volatility[current_symbol] = params.iloc[0]["dollar_volatility"]

            self.current_unit_size[current_symbol] = int(math.floor(0.01 * context.portfolio.portfolio_value /
                                                                    self.current_dollar_volatility[current_symbol]))
        else:
            self.current_high_entry[current_symbol] = None
            self.current_low_entry[current_symbol] = None

    def set_last_range_params(self, context, current_time, current_symbol):

        if self.range_time_frame == "hour":
            if current_time.minute == 59:
                current_range_data = self.range_data[current_symbol]
                self.set_range_params(current_range_data.loc[current_range_data["date"] == current_time],
                                      context,
                                      current_symbol)
            else:
                pass
        elif self.range_time_frame == "day":
            if current_time.hour == 23 and current_time.minute == 59:
                current_range_data = self.range_data[current_symbol]
                self.set_range_params(current_range_data.loc[current_range_data["date"] == current_time],
                                      context,
                                      current_symbol)
            else:
                pass

    def initial_trade_params(self, current_symbol):

        self.trades_left[current_symbol] = 4
        self.last_trade_price[current_symbol] = None
        self.next_approved_trade_price[current_symbol] = None
        self.stop_loss_price[current_symbol] = None
        self.long_is_active[current_symbol] = False
        self.short_is_active[current_symbol] = False

        if self.is_cross_symbol(current_symbol):

            self.cross_symbols_positions[current_symbol]["long"] = 0
            self.cross_symbols_positions[current_symbol]["short"] = 0

        else:
            self.last_position_amount[current_symbol] = 0

    def open_position_log(self, action, current_time, current_price, current_symbol):

        if current_symbol in self.cross_symbols:
            print("current amount cross symbol long position", self.cross_symbols_positions[current_symbol]["long"],
                  "current amount cross symbol short position", self.cross_symbols_positions[current_symbol]["short"])
        else:
            print("current amount", self.last_position_amount[current_symbol])

        print("current time", current_time,
              "current price", current_price,
              "maximum high" if action == "buy" else "minimum low",
              self.current_high_entry[current_symbol] if action == "buy" else self.current_low_entry[current_symbol])

        print("trades left", self.trades_left[current_symbol])
        print("price change permission", self.price_change_permission[current_symbol])
        print("stop loss permission", self.stop_loss_permission[current_symbol])
        print("long is active", self.long_is_active[current_symbol])
        print("short is active", self.short_is_active[current_symbol])

        if current_symbol not in self.cross_symbols:
            pass
        else:
            print("unit size", self.current_unit_size[current_symbol],
                  "current dollar volatility", self.current_dollar_volatility[current_symbol])

    def set_trade_params_log(self, current_symbol, current_time, current_price):

        print("set trade params for symbol", current_symbol)
        print("current time", current_time, "current price", current_price)
        print("ATR/2", self.current_average_true_range[current_symbol] / 2,
              "next approved price", self.next_approved_trade_price[current_symbol])

    def set_stop_loss_logs(self, action, context, current_symbol, current_time, current_price):

        print("stop loss, ", "close long position for symbol" if action == "buy" else "close short position for symbol",
              current_symbol)
        print("current time", current_time, "current price", current_price)
        print("stop loss price", self.stop_loss_price[current_symbol])
        print("portfolio value", context.portfolio.portfolio_value)

    def handle_data(self, context, data):

        current_time = pd.Timestamp(get_datetime())

        for current_symbol in self.symbols:

            current_price = data.current(symbol(current_symbol), "price")

            self.set_last_range_params(context, current_time, current_symbol)

            if current_symbol not in self.forbidden_symbols:

                # Open long position
                if self.order_not_exists(current_symbol) and self.trades_left[current_symbol] > 0 \
                        and not self.short_is_active[current_symbol]:
                    if self.current_high_entry[current_symbol]:
                        if current_price > self.current_high_entry[current_symbol]:
                            if self.trades_left[current_symbol] == 4:
                                print("buy initial trade", current_symbol)
                                if self.is_cross_symbol(current_symbol):
                                    self.open_cross_symbol_position("buy", current_symbol)
                                else:
                                    order(symbol(current_symbol), self.current_unit_size[current_symbol])
                                    self.last_position_amount[current_symbol] = \
                                        self.last_position_amount[current_symbol] + \
                                        self.current_unit_size[current_symbol]
                                self.trades_left[current_symbol] = self.trades_left[current_symbol] - 1
                                self.price_change_permission[current_symbol] = True
                                self.stop_loss_permission[current_symbol] = True
                                self.last_trade_price[current_symbol] = current_price
                                self.long_is_active[current_symbol] = True
                                self.short_is_active[current_symbol] = False
                                self.open_position_log("buy", current_time, current_price, current_symbol)

                            elif self.stop_loss_price[current_symbol] \
                                    and self.next_approved_trade_price[current_symbol] \
                                    and self.long_is_active[current_symbol] > 0 \
                                    and current_price > self.next_approved_trade_price[current_symbol]:
                                print("buy additional trade", current_symbol)
                                if self.is_cross_symbol(current_symbol):
                                    self.open_cross_symbol_position("buy", current_symbol)
                                else:
                                    order(symbol(current_symbol), self.current_unit_size[current_symbol])
                                    self.last_position_amount[current_symbol] = \
                                        self.last_position_amount[current_symbol] + \
                                        self.current_unit_size[current_symbol]
                                self.trades_left[current_symbol] = self.trades_left[current_symbol] - 1
                                self.price_change_permission[current_symbol] = True
                                self.last_trade_price[current_symbol] = current_price
                                self.long_is_active[current_symbol] = True
                                self.short_is_active[current_symbol] = False
                                self.open_position_log("buy", current_time, current_price, current_symbol)
                            else:
                                pass

                # Open short position
                if self.order_not_exists(current_symbol) and self.trades_left[current_symbol] > 0\
                        and not self.long_is_active[current_symbol]:
                    if self.current_low_entry[current_symbol]:
                        if current_price < self.current_low_entry[current_symbol]:
                            if self.trades_left[current_symbol] == 4:
                                print("sell initial trade", current_symbol)
                                if self.is_cross_symbol(current_symbol):
                                    self.open_cross_symbol_position("sell", current_symbol)
                                else:
                                    order(symbol(current_symbol), -1 * self.current_unit_size[current_symbol])
                                    self.last_position_amount[current_symbol] = \
                                        self.last_position_amount[current_symbol] + \
                                        self.current_unit_size[current_symbol]
                                self.trades_left[current_symbol] = self.trades_left[current_symbol] - 1
                                self.price_change_permission[current_symbol] = True
                                self.stop_loss_permission[current_symbol] = True
                                self.last_trade_price[current_symbol] = current_price
                                self.long_is_active[current_symbol] = False
                                self.short_is_active[current_symbol] = True
                                self.open_position_log("sell", current_time, current_price, current_symbol)

                            elif self.stop_loss_price[current_symbol] \
                                    and self.next_approved_trade_price[current_symbol] \
                                    and self.short_is_active[current_symbol] \
                                    and current_price < self.next_approved_trade_price[current_symbol]:
                                print("sell additional trade", current_symbol)
                                if self.is_cross_symbol(current_symbol):
                                    self.open_cross_symbol_position("sell", current_symbol)
                                else:
                                    order(symbol(current_symbol), -1 * self.current_unit_size[current_symbol])
                                    self.last_position_amount[current_symbol] = \
                                        self.last_position_amount[current_symbol] + \
                                        self.current_unit_size[current_symbol]
                                self.trades_left[current_symbol] = self.trades_left[current_symbol] - 1
                                self.price_change_permission[current_symbol] = True
                                self.last_trade_price[current_symbol] = current_price
                                self.long_is_active[current_symbol] = False
                                self.short_is_active[current_symbol] = True
                                self.open_position_log("sell", current_time, current_price, current_symbol)

                # Set stop loss price,
                if self.trades_left[current_symbol] == 3 and self.trade_price(context, current_symbol) \
                        and self.stop_loss_permission[current_symbol]:
                    print("last traded price for symbol", current_symbol, self.trade_price(context, current_symbol))
                    if self.long_is_active[current_symbol]:
                        self.stop_loss_price[current_symbol] = self.trade_price(context, current_symbol) - \
                                                               (2 * self.current_average_true_range[current_symbol])
                        print("set stop loss for long", self.stop_loss_price[current_symbol],
                              "for symbol", current_symbol)
                        self.stop_loss_permission[current_symbol] = False
                    elif self.short_is_active[current_symbol]:
                        self.stop_loss_price[current_symbol] = self.trade_price(context, current_symbol) + \
                                                               (2 * self.current_average_true_range[current_symbol])
                        print("set stop loss for short", self.stop_loss_price[current_symbol],
                              "for symbol", current_symbol)
                        self.stop_loss_permission[current_symbol] = False
                    print("position for symbol", current_symbol, self.position(context, current_symbol))

                # Calculate next approved trade price
                if self.last_trade_price[current_symbol] and self.price_change_permission[current_symbol]:
                    if self.long_is_active[current_symbol]:
                        if self.trades_left[current_symbol] == 4:
                            self.next_approved_trade_price[current_symbol] = \
                                self.trade_price(context, current_symbol) + \
                                self.current_average_true_range[current_symbol] / 2
                        else:
                            self.next_approved_trade_price[current_symbol] = \
                                self.last_trade_price[current_symbol] + \
                                self.current_average_true_range[current_symbol] / 2
                        self.price_change_permission[current_symbol] = False
                        self.set_trade_params_log(current_symbol, current_time, current_price)

                    elif self.short_is_active[current_symbol]:
                        if self.trades_left[current_symbol] == 4:
                            self.next_approved_trade_price[current_symbol] = \
                                self.trade_price(context, current_symbol) - \
                                self.current_average_true_range[current_symbol] / 2
                        else:
                            self.next_approved_trade_price[current_symbol] = \
                                self.last_trade_price[current_symbol] - \
                                self.current_average_true_range[current_symbol] / 2
                        self.price_change_permission[current_symbol] = False
                        self.set_trade_params_log(current_symbol, current_time, current_price)

                # Stop Loss
                if self.position(context, current_symbol) != 0 and self.order_not_exists(current_symbol):
                    if self.long_is_active[current_symbol]:
                        if current_price < self.stop_loss_price[current_symbol]:
                            if self.is_cross_symbol(current_symbol):
                                self.close_cross_symbol_position("buy", current_symbol)
                            else:
                                order(symbol(current_symbol), -1 * self.last_position_amount[current_symbol])
                            self.initial_trade_params(current_symbol)
                            self.set_stop_loss_logs("buy", context, current_symbol, current_time, current_price)
                    elif self.short_is_active[current_symbol]:
                        if current_price > self.stop_loss_price[current_symbol]:
                            if self.is_cross_symbol(current_symbol):
                                self.close_cross_symbol_position("sell", current_symbol)
                            else:
                                order(symbol(current_symbol), self.last_position_amount[current_symbol])
                            self.initial_trade_params(current_symbol)
                            self.set_stop_loss_logs("sell", context, current_symbol, current_time, current_price)

                # Take profit
                if self.position(context, current_symbol) != 0 and self.order_not_exists(current_symbol):
                    if self.long_is_active[current_symbol] and self.current_low_exit[current_symbol]:
                        if self.trade_price(context, current_symbol) < current_price < \
                                self.current_low_exit[current_symbol]:
                            if self.is_cross_symbol(current_symbol):
                                self.close_cross_symbol_position("buy", current_symbol)
                            else:
                                order(symbol(current_symbol), -1 * self.last_position_amount[current_symbol])
                            self.initial_trade_params(current_symbol)
                            print("take profit, close long position for symbol", current_symbol)
                            print("portfolio value", context.portfolio.portfolio_value)
                    elif self.short_is_active[current_symbol] and self.current_high_exit[current_symbol]:
                        if self.trade_price(context, current_symbol) > current_price > \
                                self.current_high_exit[current_symbol]:
                            if self.is_cross_symbol(current_symbol):
                                self.close_cross_symbol_position("sell", current_symbol)
                            else:
                                order(symbol(current_symbol), self.last_position_amount[current_symbol])
                            self.initial_trade_params(current_symbol)
                            print("take profit, close short position for symbol", current_symbol)
                            print("portfolio value", context.portfolio.portfolio_value)

    def get_performance(self):

        start_session = self.end_session - timedelta(days=365) + timedelta(minutes=1)

        print(self.start_session if start_session < self.start_session else start_session)

        return zipline.run_algorithm(start=self.start_session if start_session < self.start_session else start_session,
                                     end=self.end_session,
                                     initialize=self.initialize,
                                     trading_calendar=always_open.AlwaysOpenCalendar(),
                                     capital_base=self.initial_portfolio_value,
                                     handle_data=self.handle_data,
                                     data_frequency="minute",
                                     data=self.minute_data)


symbols = ["BTCUSD", "XRPUSD", "XRPBTC"]

cross_symbols = {"XRPBTC": {"long": "XRPUSD", "short": "BTCUSD"},
                 "ETHBTC": {"long": "ETHUSD", "short": "BTCUSD"}}

# fill base symbols of cross symbol if you want to run single cross symbol or cross symbols only
forbidden_symbols = []

test_params = utils.multi_asset_with_cross_initial_test_params(symbols,
                                                               cross_symbols,
                                                               forbidden_symbols,
                                                               365,
                                                               20,
                                                               55,
                                                               20,
                                                               1000000,
                                                               "day")

result = BackTest(test_params).performance

import visualize_data

columns = ["algo_volatility",
           "algorithm_period_return",
           "benchmark_period_return",
           "benchmark_volatility",
           "shorts_count"]

visualize_data.algo_vs_benchmark(result, columns[1], columns[2])

result_string = list(set(symbols) - set(forbidden_symbols))

result_string = "_".join(result_string) if len(result_string) != 1 else result_string[0]

result.to_csv("./" + result_string + "_result.csv", header=True)
