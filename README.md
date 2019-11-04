# Backtest scripts for turtle strategy

## Installation

Create [virtual environment](https://docs.python.org/3/library/venv.html)

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install dependencies.

```bash
pip install -r requirements.txt
```
## Usage

For single asset back test use back_test.py
```python
# "BTCUSD" - Asset,
# 365 - Days to load historical data
# 20 - Average True Range
# 55 - Number of bars to calculate maximum for the last 55 "high"
# 20 - Number of bars to calculate minimum for the last 20 "low"
# 1000000 - Initial balance
# "day - Time frame used to generate buy/sell signals 
test_params = utils.initial_test_params("BTCUSD", 365, 20, 55, 20, 1000000, "day")

```

For multi asset back test with single base currency use multi_asset_back_test.py
```python
# ["BTCUSD", "ETHUSD", "XRPUSD"] - Assets,
# 365 - Days to load historical data
# 20 - Average True Range
# 55 - Number of bars to calculate maximum for the last 55 "high"
# 20 - Number of bars to calculate minimum for the last 20 "low"
# 1000000 - Initial balance
# "day - Time frame used to generate buy/sell signals

symbols = ["BTCUSD", "ETHUSD", "XRPUSD"]
 
test_params = utils.multi_asset_initial_test_params(symbols, 365, 20, 55, 20, 1000000, "day")

```

For multi asset back test with multi base currencies use multi_asset_cross_back_test.py

```python
# ["BTCUSD", "ETHUSD", "XRPUSD"] - Assets
# {"XRPBTC": {"long": "XRPUSD", "short": "BTCUSD"},
#  "ETHBTC": {"long": "ETHUSD", "short": "BTCUSD"}} - assets with different base currency
# 365 - Days to load historical data
# 20 - Average True Range
# 55 - Number of bars to calculate maximum for the last 55 "high"
# 20 - Number of bars to calculate minimum for the last 20 "low"
# 1000000 - Initial balance
# "day - Time frame used to generate buy/sell signals


symbols = ["BTCUSD", "ETHUSD", "XRPUSD", "XRPBTC", "ETHBTC"]

cross_symbols = {"XRPBTC": {"long": "XRPUSD", "short": "BTCUSD"},
                 "ETHBTC": {"long": "ETHUSD", "short": "BTCUSD"}}

test_params = utils.multi_asset_with_cross_initial_test_params(symbols, cross_symbols, 365, 20, 55, 20, 1000000, "day")
```

## pyfolio

uncomment following in script

```python
returns, positions, transactions = pf.utils.extract_rets_pos_txn_from_zipline(result)
pf.create_full_tear_sheet(returns, positions=positions, transactions=transactions, round_trips=True)
```
 
```bash
jupyter notebook
```

Load back test file in jupyter notebook page


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
Michael Stennicke
