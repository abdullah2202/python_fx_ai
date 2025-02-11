# from api.env import api_details
# from oandapyV20 import API
import candles as CC
from datetime import datetime, timedelta

candles = []
cc = CC.Candles()
num_of_candles = 2

# Define the time range (e.g., last 7 days)
end_time = datetime.now() - timedelta(hours=1)
start_time = end_time - timedelta(weeks=20)

# Convert to RFC3339 format (required by OANDA)
from_time = start_time.isoformat("T") + "Z"
to_time = end_time.isoformat("T") + "Z"

print("Start Time: ",start_time)
print("End Time: ", end_time)

# Set granularity of candle data to get back, e.g. 30M, 4H, 1D
cc.setGranularity("D")

# Get candle data by time, set start and to
candles = cc.getCandleDataByTime(num_of_candles,from_time,to_time)

# Get candle data based on number of candles received
# candles = cc.getCandleData(num_of_candles)

# Iterate over candle data and print each one
for candle in candles:

   # Print the 'mid' for each candle object.
   print(candle['time']," - OHLC:", candle['mid'])
   # print(candle)

# Print previous 4H candle
# print("\nPrevious 4H Candle:", candles[1]['mid'])

