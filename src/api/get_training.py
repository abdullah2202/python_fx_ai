from env import api_details
from oandapyV20 import API
from oandapyV20.exceptions import V20Error
from oandapyV20.endpoints.instruments import InstrumentsCandles
import pandas as pd
import time
import datetime
import os

# OANDA API credentials
ACCOUNT_ID = api_details.account_id
ACCESS_TOKEN = api_details.oanda_token
INSTRUMENT = "XAU_USD"

# Initialize the OANDA API client
api = API(access_token=ACCESS_TOKEN)

# File to store breakout data
# BREAKOUT_CSV = "breakout_data.csv"
BREAKOUT_CSV = "data.csv"

# Function to check if bullish candle
def is_bullish(candle):
    return candle["open"] > candle["close"]

# Function to check if bearish candle
def is_bearish(candle):
    return candle["open"] < candle["close"]

# Function to check if candle is in london session
def is_in_london_session(candle):
    """Checks if a candle's time (UTC) falls within the London session (10 AM - 4 PM UTC)."""

    candle_time = candle["time"]

    # Handle string times (if needed):
    if isinstance(candle_time, str):
        candle_time = datetime.datetime.fromisoformat(candle_time.replace('Z', '+00:00')) # Handles 'Z' for UTC
    
    # Ensure the datetime object is timezone-aware. If it's naive, assume UTC.
    if candle_time.tzinfo is None:
      candle_time = candle_time.replace(tzinfo=datetime.timezone.utc)

    start_time = datetime.time(10, 0, 0, tzinfo=datetime.timezone.utc)  # 10:00 AM UTC (timezone-aware)
    end_time = datetime.time(16, 0, 0, tzinfo=datetime.timezone.utc)    # 4:00 PM UTC (timezone-aware)

    start_datetime = datetime.datetime.combine(candle_time.date(), start_time)
    end_datetime = datetime.datetime.combine(candle_time.date(), end_time)

    return start_datetime <= candle_time <= end_datetime


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


# Function to get multiple api requests
def fetch_multiple_data(start_date_str, end_date_str):  # Accept date strings
    # Start with empty DataFrame
    all_df = pd.DataFrame()

    # Convert date strings to datetime.date objects
    start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date() # Example format, adjust if needed
    end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()   # Example format, adjust if needed

    current_date = start_date

    while current_date < end_date:
        # Request data for 90 days at a time
        period_end = current_date + datetime.timedelta(days=90)
        
        if period_end > end_date:
            period_end = end_date

        data = fetch_historical_data(current_date, period_end)

        # print("Type: ", type(data))

        if isinstance(data, pd.DataFrame): # Check if data is a DataFrame before concatenation
            all_df = pd.concat([all_df, data], ignore_index=True) # Concatenate DataFrames
        elif data is not None: # Handle other data types or None as needed
            print("Data is not a DataFrame, skipping concatenation.")
            print(data) # Print or log the non-DataFrame data for debugging

        current_date = period_end

    return all_df

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
            # if resistance is None or new_resistance > resistance :
            if resistance is None or resistance <= new_resistance <= resistance + 2.0:
                resistance = new_resistance
                # print(f"New Resistance Level: {resistance}")

        # Check if the previous candle is bearish and the current candle is bullish
        elif previous_candle["close"] < previous_candle["open"] and current_candle["close"] > current_candle["open"]:
            new_support = previous_candle["close"]

            if support is None or support >= new_support >= support - 2.0:
                support = new_support
                # print(f"New Support Level: {support}")

    return support, resistance

# Function to check if a candle breaks support or resistance
def check_breakout(candle, support, resistance):
    open_price = candle["open"]
    close_price = candle["close"]

    # Check for resistance breakout
    if resistance is not None and open_price < resistance and close_price > resistance:
        # print(candle["time"])
        print(f"{candle['time']} -  Resistance broken at {resistance}")
        return "resistance"

    # Check for support breakout
    if support is not None and open_price > support and close_price < support:
        # print(candle["time"])
        print(f"{candle['time']} -  Support broken at {support}")
        return "support"

    # No breakout
    return None

# Function to log breakout data to a CSV file
def log_breakout_to_csv(candle, candle1, candle2, candle3, candle4, breakout_type, support, resistance):
    # Create a dictionary with the breakout data
    breakout_data = {
        "time": candle["time"],
        "size": abs(candle["close"]-candle["open"]),
        "volume": candle["volume"],
        "Candle1Size": abs(candle1["close"]-candle1["open"]),
        "Candle2Size": abs(candle2["close"]-candle2["open"]),
        "Candle3Size": abs(candle3["close"]-candle3["open"]),
        "Candle4Size": abs(candle4["close"]-candle4["open"]),
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
    # df = fetch_historical_data(start_time, end_time)
    df = fetch_multiple_data(start_time, end_time)

    if df is None:
        print("Failed to fetch historical data. Exiting...")
        return

    # Initialize support and resistance levels
    support = None
    resistance = None

    # Iterate through the historical data one candle at a time
    for i in range(len(df)):
        candle = df.iloc[i]

        # Check if candle is in London session only
        if is_in_london_session(candle):

            # Update support and resistance levels using the last 100 candles
            if i >= 100:
                support, resistance = detect_support_resistance(df.iloc[:i], num_candles=100)

            # Check for breakouts
            breakout = check_breakout(candle, support, resistance)
            if breakout:
                # print(f"Breakout detected: {breakout}")

                if i + 1 < len(df):
                    next_candle = df.iloc[i + 1]

                    #Check if breaking candle and next candle are same direction
                    if (is_bullish(candle) and is_bullish(next_candle))  or (is_bearish(candle) and is_bearish(next_candle)):

                        candle1 = candle
                        candle2 = df.iloc[i-1]
                        candle3 = df.iloc[i-2]
                        candle4 = df.iloc[i-3]

                        # Log the breakout to the CSV file
                        log_breakout_to_csv(next_candle, candle1, candle2, candle3, candle4, breakout, support, resistance)

                        i += 1

    print("Backtest complete.")




# Run the continuous detection
# run_continuously()


start_date_str = "2024-01-01"
end_date_str = "2024-12-31"

# Run the backtest
backtest(start_date_str, end_date_str)
