from env import api_details
from oandapyV20 import API
import oandapyV20.endpoints.instruments as instruments
import numpy as np

class Candles():

   instrument = 'XAU_USD'
   candle_list = []
   api = API(access_token=api_details.oanda_token)
   granularity = 'M30'
   useCache = False
   candle_data = []

   def __init__(self):
      pass

   def loadCandleData(self, num_of_candles):
      self.candle_data = self.getCandleData(num_of_candles)

   def getHigh(self, shift):
      if self.getUseCache():
         return self.candle_data[shift]['mid']['h']
      return self.getCandleInfo(shift, 'h')

   def getLow(self, shift):
      if self.getUseCache():
         return self.candle_data[shift]['mid']['l']
      return self.getCandleInfo(shift, 'l')
   
   def getOpen(self, shift):
      if self.getUseCache():
         return self.candle_data[shift]['mid']['o']
      return self.getCandleInfo(shift, 'o')
   
   def getClose(self, shift):
      if self.getUseCache():
         return self.candle_data[shift]['mid']['o']
      return self.getCandleInfo(shift, 'c')
   
   def getVolume(self, shift):
      if self.getUseCache():
         return self.candle_data[shift]['volume']
      return self.getCandleMeta(shift, 'volume')

   def setGranularity(self, granularity):
      self.granularity = granularity
   
   def getGranularity(self):
      return self.granularity
   
   def setInstrument(self, instrument):
      self.instrument = instrument

   def getInstrument(self):
      return self.instrument
   
   def setUseCache(self, useCache):
      self.useCache = useCache
   
   def getUseCache(self):
      return self.useCache
   
   def isBearish(self, shift):
      if self.getUseCache():
         candle = self.candle_data[shift]['mid']
      else:
         candle = self.getCandleMeta(shift, 'mid')
      return candle['o'] > candle['c']
   
   def isBullish(self, shift):
      if self.getUseCache():
         candle = self.candle_data[shift]['mid']
      else:
         candle = self.getCandleMeta(shift, 'mid')
      return candle['c'] >= candle['o']

   def getCandleInfo(self, shift, type):
      res = self.getCandleData(shift+1)
      return res[shift]['mid'][type]

   def getCandleMeta(self, shift, type):
      res = self.getCandleData(shift+1)
      return res[shift][type]

   def getCandleData(self, num_of_candles):
      params = {'granularity' : self.getGranularity(), 'count' : num_of_candles}
      r = instruments.InstrumentsCandles(instrument=self.getInstrument(), params=params)
      self.api.request(r)
      candles = np.flip(r.response['candles'])
      return candles
      
   def getCandleDataByTime(self, num_of_candles, start_time, end_time):
      params = {'granularity' : self.getGranularity(), 'from' : start_time, 'to' : end_time, 'price' : 'M'}
      r = instruments.InstrumentsCandles(instrument=self.getInstrument(), params=params)
      self.api.request(r)
      candles = np.flip(r.response['candles'])
      return candles

