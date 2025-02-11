from env import api_details
from oandapyV20 import API
from oandapyV20.exceptions import V20Error
from oandapyV20.endpoints.instruments import InstrumentsCandles
import pandas as pd
import time
from datetime import datetime, timedelta
import os

# OANDA API credentials
ACCOUNT_ID = api_details.account_id
ACCESS_TOKEN = api_details.oanda_token
INSTRUMENT = "XAU_USD"

# Initialize the OANDA API client
api = API(access_token=ACCESS_TOKEN)

# File to store breakout data
BREAKOUT_CSV = "breakout_data.csv"

# Function to fetch candlestick data
def fetch_candlestick_data(start_time, end_time):
    params = {
        "granularity": "M30",  # 30-minute candles
        "from": start_time,    # Start time
        "to": end_time,        # End time
        "price": "M",          # Midpoint candles (optional: "B" for bid, "A" for ask)
    }

    try:
        # Create the request
        request = InstrumentsCandles(instrument=INSTRUMENT, params=params)

        # Make the API call
        response = api.request(request)

        # Parse the response into a DataFrame
        candles = response.get("candles", [])
        data = []

        for candle in candles:
            data.append({
                "time": candle["time"],
                "open": float(candle["mid"]["o"]),
                "high": float(candle["mid"]["h"]),
                "low": float(candle["mid"]["l"]),
                "close": float(candle["mid"]["c"]),
                "volume": int(candle["volume"]),
            })

        df = pd.DataFrame(data)
        df["time"] = pd.to_datetime(df["time"])
        return df

    except V20Error as e:
        print(f"An error occurred while fetching data: {e}")
        return None

# Function to fetch historical candlestick data
def fetch_historical_data(start_time, end_time, granularity="M30"):
    params = {
        "granularity": granularity,  # 30-minute candles
        "from": start_time,          # Start time
        "to": end_time,              # End time
        "price": "M",                # Midpoint candles (optional: "B" for bid, "A" for ask)
    }

    try:
        # Create the request
        request = InstrumentsCandles(instrument=INSTRUMENT, params=params)

        # Make the API call
        response = api.request(request)

        # Parse the response into a DataFrame
        candles = response.get("candles", [])
        data = []

        for candle in candles:
            data.append({
                "time": candle["time"],
                "open": float(candle["mid"]["o"]),
                "high": float(candle["mid"]["h"]),
                "low": float(candle["mid"]["l"]),
                "close": float(candle["mid"]["c"]),
                "volume": int(candle["volume"]),
            })

        df = pd.DataFrame(data)
        df["time"] = pd.to_datetime(df["time"])
        return df

    except V20Error as e:
        print(f"An error occurred while fetching data: {e}")
        return None


# Function to detect support and resistance levels
def detect_support_resistance(df, num_candles=100):
    support = None
    resistance = None

    # Iterate through the last `num_candles` candles in reverse order
    for i in range(len(df) - 1, max(len(df) - num_candles - 1, 0), -1):
        current_candle = df.iloc[i]
        previous_candle = df.iloc[i - 1]

        # Check if the previous candle is bullish and the current candle is bearish
        if previous_candle["close"] > previous_candle["open"] and current_candle["close"] < current_candle["open"]:
            new_resistance = previous_candle["close"]
            if resistance is None or new_resistance > resistance:
                resistance = new_resistance
                print(f"New Resistance Level: {resistance}")

        # Check if the previous candle is bearish and the current candle is bullish
        elif previous_candle["close"] < previous_candle["open"] and current_candle["close"] > current_candle["open"]:
            new_support = previous_candle["close"]
            if support is None or new_support < support:
                support = new_support
                print(f"New Support Level: {support}")

    return support, resistance

# Function to check if a candle breaks support or resistance
def check_breakout(candle, support, resistance):
    open_price = candle["open"]
    close_price = candle["close"]

    # Check for resistance breakout
    if resistance is not None and open_price < resistance and close_price > resistance:
        print(f"Resistance broken at {resistance}!")
        return "resistance"

    # Check for support breakout
    if support is not None and open_price > support and close_price < support:
        print(f"Support broken at {support}!")
        return "support"

    # No breakout
    return None

# Function to log breakout data to a CSV file
def log_breakout_to_csv(candle, breakout_type, support, resistance):
    # Create a dictionary with the breakout data
    breakout_data = {
        "time": candle["time"],
        "open": candle["open"],
        "high": candle["high"],
        "low": candle["low"],
        "close": candle["close"],
        "volume": candle["volume"],
        "breakout_type": breakout_type,
        "support_level": support,
        "resistance_level": resistance,
    }

    # Convert the dictionary to a DataFrame
    df = pd.DataFrame([breakout_data])

    # Append the data to the CSV file
    if not os.path.exists(BREAKOUT_CSV):
        # Create the file if it doesn't exist
        df.to_csv(BREAKOUT_CSV, index=False)
    else:
        # Append to the existing file
        df.to_csv(BREAKOUT_CSV, mode="a", header=False, index=False)

    print(f"Breakout logged to {BREAKOUT_CSV}")

# Function to run the detection continuously
def run_continuously():
    print("Starting continuous support/resistance detection...")

    while True:
        # Get the current time and calculate the start time for the last 100 candles
        now = datetime.now()
        start_time = (now - timedelta(minutes=30 * 100)).strftime("%Y-%m-%dT%H:%M:%SZ")
        end_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Fetch the latest candlestick data
        df = fetch_candlestick_data(start_time, end_time)
        if df is None:
            print("Failed to fetch data. Retrying in 1 minute...")
            time.sleep(60)  # Wait 1 minute before retrying
            continue

        # Detect support and resistance levels
        support, resistance = detect_support_resistance(df)
        print(f"Current Support Level: {support}")
        print(f"Current Resistance Level: {resistance}")

        # Check the latest candle for breakouts
        latest_candle = df.iloc[-1]
        breakout = check_breakout(latest_candle, support, resistance)
        if breakout:
            print(f"Breakout detected: {breakout}")
            # Log the breakout to the CSV file
            log_breakout_to_csv(latest_candle, breakout, support, resistance)

        # Wait until the next 30-minute candle starts
        next_candle_time = (now + timedelta(minutes=30)).replace(second=0, microsecond=0)
        sleep_duration = (next_candle_time - now).total_seconds()
        print(f"Waiting for the next 30-minute candle at {next_candle_time}...")
        time.sleep(sleep_duration)

# Function to backtest over a specific period
def backtest(start_time, end_time):
    print(f"Starting backtest from {start_time} to {end_time}...")

    # Fetch historical data for the specified period
    df = fetch_historical_data(start_time, end_time)
    if df is None:
        print("Failed to fetch historical data. Exiting...")
        return

    # Initialize support and resistance levels
    support = None
    resistance = None

    # Iterate through the historical data one candle at a time
    for i in range(len(df)):
        candle = df.iloc[i]
        print(f"Processing candle at {candle['time']}...")

        # Update support and resistance levels using the last 100 candles
        if i >= 100:
            support, resistance = detect_support_resistance(df.iloc[:i], num_candles=100)

        # Check for breakouts
        breakout = check_breakout(candle, support, resistance)
        if breakout:
            print(f"Breakout detected: {breakout}")
            # Log the breakout to the CSV file
            log_breakout_to_csv(candle, breakout, support, resistance)

    print("Backtest complete.")




# Run the continuous detection
# run_continuously()


# Define the backtest period
start_time = "2023-01-01T00:00:00Z"  # Start time in UTC
end_time = "2023-01-31T23:59:59Z"    # End time in UTC

# Run the backtest
backtest(start_time, end_time)









