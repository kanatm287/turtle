#!/bin/bash

DIR=`dirname $0`

PY_VERSION=$(python3 --version)

cd "$DIR"

python -V

python -m pip install --upgrade pip setuptools wheel

pip install -r requirements.txt

zipline bundles

SOURCE_FILE="$DIR/calendar_utils.py"
if [[ $(python3 --version | grep 3.6) ]]; then
    DST_DIR="$DIR/venv/lib/python3.6/site-packages/trading_calendars/"
else
    DST_DIR="$DIR/venv/lib/python3.5/site-packages/trading_calendars/"
fi

cp "$DIR/$SOURCE_FILE" "$DST_DIR"

SOURCE_FILE="$DIR/benchmarks.py"
if [[ $(python3 --version | grep 3.6) ]]; then
    DST_DIR="$DIR/venv/lib/python3.6/site-packages/zipline/data/"
else
    DST_DIR="$DIR/venv/lib/python3.5/site-packages/zipline/data/"
fi

cp "$DIR/$SOURCE_FILE" "$DST_DIR"
