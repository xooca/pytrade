import pandas as pd
import numpy as np
import datetime as dt
#import statsmodels.api as sm
#from stocktrends import Renko
from talib.abstract import *

class signals_old:
    def __init__(self,file):
        self.df = pd.read_csv(file,encoding='latin-1',index_col=['Unnamed: 0'])
        self.df = self.df[self.df['Open']!='-']
        #self.df = self.df.replace('-', '0')
        self.df['High'] = self.df['High'].astype('float')
        self.df['Low'] = self.df['Low'].astype('float')
        self.df['Open'] = self.df['Open'].astype('float')
        self.df['Close*'] = self.df['Close*'].astype('float')
        self.df['Adj. close**'] = self.df['Adj. close**'].astype(float)
        self.df['Volume'] = self.df['Volume'].str.replace(',', '').replace('-', 0)
        self.df['Volume'] = self.df['Volume'].astype(float)
        self.df.rename(columns = { "Open" : "open","High" : "high","Low" : "low","Close*":"act_close","Adj. close**" : "close", "Volume" : "volume"}, inplace = True)
        self.df.index.name = 'date'
        self.df.index = pd.to_datetime(self.df.index)

    def macd(self,a=12,b=26,c=9):
        """function to calculate MACD
        typical values a = 12; b =26, c =9"""
        self.df["ma_fast"]=self.df["close"].ewm(span=a,min_periods=a).mean()
        self.df["ma_slow"]=self.df["close"].ewm(span=b,min_periods=b).mean()
        self.df["macd"]=self.df["ma_fast"]-self.df["ma_slow"]
        self.df["signal"]=self.df["macd"].ewm(span=c,min_periods=c).mean()
        #Signal-MACD : Negative is Bearish and Positive is Bullish
        self.df["signal-macd"] = self.df["signal"] - self.df["macd"]

    def atr(self,n=20):
        "function to calculate True Range and Average True Range"
        self.df['high-low']=abs(self.df['high']-self.df['low'])
        self.df['high-previousclose']=abs(self.df['high']-self.df['close'].shift(1))
        self.df['low-previousclose']=abs(self.df['low']-self.df['close'].shift(1))
        self.df['tr']=self.df[['high-low','high-previousclose','low-previousclose']].max(axis=1,skipna=False)
        # Low ATR value represents less volatility
        self.df['atr'] = self.df['tr'].rolling(n).mean()
        #df['ATR'] = df['TR'].ewm(span=n,adjust=False,min_periods=n).mean()
        #df2 = df.drop(['H-L','H-PC','L-PC'],axis=1)


    def bollinger_band(self,n=20):
        "function to calculate Bollinger Band"
        self.df["moving_average"] = self.df['close'].rolling(n).mean()
        self.df["upper_bollinger_band"] = self.df["moving_average"] + 2*self.df['close'].rolling(n).std(ddof=0) 
        self.df["lower_bollinger_band"] = self.df["moving_average"] - 2*self.df['close'].rolling(n).std(ddof=0)
        # Low BB_width value represents less volatility
        self.df["bolinger_band_width"] = self.df["upper_bollinger_band"] - self.df["lower_bollinger_band"]
        #self.df.dropna(inplace=True)

    def rsi(self, n=15):
        "function to calculate RSI"
        delta = self.df["close"].diff().dropna()
        u = delta * 0
        d = u.copy()
        u[delta > 0] = delta[delta > 0]
        d[delta < 0] = -delta[delta < 0]
        u[u.index[n-1]] = np.mean( u[:n]) # first value is average of gains
        u = u.drop(u.index[:(n-1)])
        d[d.index[n-1]] = np.mean( d[:n]) # first value is average of losses
        d = d.drop(d.index[:(n-1)])
        rs = u.ewm(com=n,min_periods=n).mean()/d.ewm(com=n,min_periods=n).mean()
        # RSI above 70 (80 incase of india) is overbought and below 30 (20 incase of india) is oversold
        self.df['rsi'] = 100 - 100 / (1+rs)

    def adx(self,n):
        "function to calculate ADX"
        if 'tr' not in self.df.columns.tolist():
            self.atr(n) #the period parameter of ATR function does not matter because period does not influence TR calculation
        self.df['dm_plus']=np.where((self.df['high']-self.df['high'].shift(1))>(self.df['low'].shift(1)-self.df['low']),self.df['high']-self.df['high'].shift(1),0)
        self.df['dm_plus']=np.where(self.df['dm_plus']<0,0,self.df['dm_plus'])
        self.df['dm_minus']=np.where((self.df['low'].shift(1)-self.df['low'])>(self.df['high']-self.df['high'].shift(1)),self.df['low'].shift(1)-self.df['low'],0)
        self.df['dm_minus']=np.where(self.df['dm_minus']<0,0,self.df['dm_minus'])
        TRn = []
        DMplusN = []
        DMminusN = []
        TR = self.df['tr'].tolist()
        DMplus = self.df['dm_plus'].tolist()
        DMminus = self.df['dm_minus'].tolist()
        for i in range(len(self.df)):
            if i < n:
                TRn.append(np.NaN)
                DMplusN.append(np.NaN)
                DMminusN.append(np.NaN)
            elif i == n:
                TRn.append(self.df['tr'].rolling(n).sum().tolist()[n])
                DMplusN.append(self.df['dm_plus'].rolling(n).sum().tolist()[n])
                DMminusN.append(self.df['dm_minus'].rolling(n).sum().tolist()[n])
            elif i > n:
                TRn.append(TRn[i-1] - (TRn[i-1]/n) + TR[i])
                DMplusN.append(DMplusN[i-1] - (DMplusN[i-1]/n) + DMplus[i])
                DMminusN.append(DMminusN[i-1] - (DMminusN[i-1]/n) + DMminus[i])
        self.df['tr_n'] = np.array(TRn)
        self.df['dm_plus_n'] = np.array(DMplusN)
        self.df['dm_minus_n'] = np.array(DMminusN)
        self.df['di_plus_n']=100*(self.df['dm_plus_n']/self.df['tr_n'])
        self.df['di_minus_n']=100*(self.df['dm_minus_n']/self.df['tr_n'])
        self.df['di_diff']=abs(self.df['di_plus_n']-self.df['di_minus_n'])
        self.df['di_sum']=self.df['di_plus_n']+self.df['di_minus_n']
        self.df['dx']=100*(self.df['di_diff']/self.df['di_sum'])
        ADX = []
        DX = self.df['dx'].tolist()
        for j in range(len(self.df)):
            if j < 2*n-1:
                ADX.append(np.NaN)
            elif j == 2*n-1:
                ADX.append(self.df['dx'][j-n+1:j+1].mean())
            elif j > 2*n-1:
                ADX.append(((n-1)*ADX[j-1] + DX[j])/n)
        # ADX :  00-25 : Absent or weak trend
        #        25-50 : Strong Trend
        #        50-75 : Very strong Trend
        #        75-100: Extremely strong Trend
        self.df['adx']=np.array(ADX)


    def obv(self):
        """Leading Market Indicator 
            Its a Momentum Indicator
            Its generates lots of false indicator
            Used in conjunction with lagging indicator like MACD
            function to calculate On Balance Volume
            > Rising OBV indicated positive volume pressure that can lead to higher prices
            > Falling OBV indicated negative volume pressure that can lead to lower prices  
        """
        self.df['daily_ret'] = self.df['close'].pct_change()
        self.df['direction'] = np.where(self.df['daily_ret']>=0,1,-1)
        self.df['direction'][0] = 0
        self.df['vol_adj'] = self.df['volume'] * self.df['direction']
        self.df['obv'] = self.df['vol_adj'].cumsum()

    def slope(self,n=5):
        "function to calculate the slope of regression line for n consecutive points on a plot"
        ser = self.df["close"]
        ser = (ser - ser.min())/(ser.max() - ser.min())
        x = np.array(range(len(ser)))
        x = (x - x.min())/(x.max() - x.min())
        slopes = [i*0 for i in range(n-1)]
        for i in range(n,len(ser)+1):
            y_scaled = ser[i-n:i]
            x_scaled = x[i-n:i]
            x_scaled = sm.add_constant(x_scaled)
            model = sm.OLS(y_scaled,x_scaled)
            results = model.fit()
            slopes.append(results.params[-1])
        slope_angle = (np.rad2deg(np.arctan(np.array(slopes))))
        self.df['slope'] = np.array(slope_angle)

    def renko_chart_df(self,n=120):
        "function to convert ohlc data into renko bricks"
        df = self.df.copy()
        df.reset_index(inplace=True)
        df = df[['date','high','low','open','close','volume']]
        print(df.dtypes)
        renko_df = Renko(df)
        if 'tr' not in self.df.columns.tolist():
            self.atr(n)
        renko_df.brick_size = round(self.df["atr"][-1],0)
        del df
        df = renko_df.get_ohlc_data()
        df = df.set_index('date')
        df = df[['uptrend']]
        self.df = self.df.join(df, how='left')
    
    def __call__(self):
        self.macd()


class signals:
    def __init__(self,file):
        self.df = pd.read_csv(file,encoding='latin-1',index_col=['Unnamed: 0'])
        self.df = self.df[self.df['Open']!='-']
        self.df['Volume'] = self.df['Volume'].str.replace(',','').replace('-','0').astype('float')
        self.df.index.name = 'date'
        self.df.index = pd.to_datetime(self.df.index)
        self.df = self.df.sort_index()
        for col in self.df.columns.tolist()[:-1]:
            self.df[col] = self.df[col].str.replace(',','').astype('float')

        self.high = np.array(self.df['High'])
        self.low = np.array(self.df['Low'])
        self.open = np.array(self.df['Open'])
        self.close = np.array(self.df['Close*'])
        self.adjclose = np.array(self.df['Adj. close**'])
        self.volume = np.array(self.df['Volume'])

    def momentum_ADX(self,timeperiod=14):
        self.df['momentum_ADX'] = ADX(self.high,self.low,self.close,timeperiod) 

    def momentum_ADXR(self,timeperiod=14):
        self.df['momentum_ADXR'] = ADXR(self.high,self.low,self.close,timeperiod) 

    def momentum_APO(self,fastperiod=12, slowperiod=26, matype=0):
        self.df['momentum_APO'] = APO(self.close,fastperiod, slowperiod, matype) 

    def momentum_AROON(self,timeperiod=14):
        self.df['momentum_AROON_DOWN'],self.df['momentum_AROON_UP'] = AROON(self.high,self.low,self.close,timeperiod) 

    def momentum_AROONOSC(self,timeperiod=14):
        self.df['momentum_AROONOSC']= AROONOSC(self.high,self.low,self.close,timeperiod)

    def momentum_BOP(self,timeperiod=14):
        self.df['momentum_BOP']= BOP(self.open,self.high,self.low,self.close,timeperiod)
   
    def momentum_CCI(self,timeperiod=14):
        self.df['momentum_CCI']= CCI(self.high,self.low,self.close,timeperiod)

    def momentum_CMO(self,timeperiod=14):
        self.df['momentum_CMO']= CMO(self.close,timeperiod)

    def momentum_DX(self,timeperiod=14):
        self.df['momentum_DX']= DX(self.high,self.low,self.close,timeperiod)

    def momentum_MACD(self,fastperiod=12, slowperiod=26, signalperiod=9):
        self.df['momentum_MACD'],self.df['momentum_MACD_SIGNAL'],self.df['momentum_MACD_HIST'] = MACD(self.close,fastperiod, slowperiod, signalperiod)

    def momentum_MACDEXT(self,fastperiod=12, fastmatype=0, slowperiod=26, slowmatype=0, signalperiod=9, signalmatype=0):
        self.df['momentum_MACDEXT'],self.df['momentum_MACDEXT_SIGNAL'],self.df['momentum_MACDEXT_HIST'] = MACDEXT(self.close,fastperiod, fastmatype, slowperiod, slowmatype, signalperiod, signalmatype)

    def momentum_MACDFIX(self,signalperiod=9):
        self.df['momentum_MACDFIX'],self.df['momentum_MACDFIX_SIGNAL'],self.df['momentum_MACDFIX_HIST'] = MACDFIX(self.close,signalperiod)

    def momentum_MFI(self,timeperiod=14):
        self.df['momentum_MFI']= MFI(self.high,self.low,self.close,self.volume,timeperiod)

    def momentum_MINUS_DM(self,timeperiod=14):
        self.df['momentum_MINUS_DM']= MINUS_DM(self.high,self.low,timeperiod)

    def momentum_MOM(self,timeperiod=10):
        self.df['momentum_MOM']= MOM(self.low,timeperiod)

    def momentum_PLUS_DI(self,timeperiod=14):
        self.df['momentum_PLUS_DI']= PLUS_DI(self.high,self.low,self.close,timeperiod)

    def momentum_PLUS_DM(self,timeperiod=14):
        self.df['momentum_PLUS_DM']= PLUS_DM(self.high,self.low,timeperiod)

    def momentum_PPO(self,fastperiod=12, slowperiod=26, matype=0):
        self.df['momentum_PPO']= PPO(self.close,fastperiod, slowperiod, matype)

    def momentum_ROC(self,timeperiod=10):
        self.df['momentum_ROC']= ROC(self.close,timeperiod)

    def momentum_ROCP(self,timeperiod=10):
        self.df['momentum_ROCP']= ROCP(self.close,timeperiod)

    def momentum_ROCR(self,timeperiod=10):
        self.df['momentum_ROCR']= ROCR(self.close,timeperiod)

    def momentum_ROCR100(self,timeperiod=10):
        self.df['momentum_ROCR100']= ROCR100(self.close,timeperiod)

    def momentum_RSI(self,timeperiod=14):
        self.df['momentum_RSI']= RSI(self.close,timeperiod)

    def momentum_STOCH(self,fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0):
        self.df['momentum_SLOWK'],self.df['momentum_SLOWD']= STOCH(self.high,self.low,self.close,fastk_period, slowk_period, slowk_matype, slowd_period, slowd_matype)

    def momentum_STOCHF(self,fastk_period=5, fastd_period=3, fastd_matype=0):
        self.df['momentum_FASTK'],self.df['momentum_FASTD']= STOCHF(self.high,self.low,self.close,fastk_period, fastd_period, fastd_matype)

    def momentum_STOCHRSI(self,timeperiod=14, fastk_period=5, fastd_period=3, fastd_matype=0):
        self.df['momentum_STOCHRSI_FASTK'],self.df['momentum_STOCHRSI_FASTD']= STOCHRSI(self.close,timeperiod, fastk_period, fastd_period, fastd_matype)

    def momentum_TRIX(self,timeperiod=30):
        self.df['momentum_TRIX']= TRIX(self.close,timeperiod)
    
    def momentum_ULTOSC(self,timeperiod1=7, timeperiod2=14, timeperiod3=28):
        self.df['momentum_ULTOSC']= ULTOSC(self.high,self.low,self.close,timeperiod1, timeperiod2, timeperiod3)

    def momentum_WILLR(self,timeperiod=14):
        self.df['momentum_WILLR'] = WILLR(self.high,self.low,self.close,timeperiod)

    def volumn_AD(self):
        self.df['volume_AD'] = AD(self.high,self.low,self.close,self.volume)

    def volumn_ADOSC(self,fastperiod=3, slowperiod=10):
        self.df['volume_ADOSC'] = ADOSC(self.high, self.low, self.close, self.volume, fastperiod, slowperiod)

    def volumn_OBV(self):
        self.df['volume_OBV'] = OBV(self.high,self.low,self.close,self.volume)

    def volatile_ATR(self,timeperiod=14):
        self.df['volatile_ATR'] = ATR(self.high,self.low,self.close,timeperiod)

    def volatile_NATR(self,timeperiod=14):
        self.df['volatile_NATR'] = NATR(self.high,self.low,self.close,timeperiod)

    def volatile_TRANGE(self):
        self.df['volatile_TRANGE'] = TRANGE(self.high,self.low,self.close)

    def transform_AVGPRICE(self):
        self.df['transform_AVGPRICE'] = AVGPRICE(self.open,self.high,self.low,self.close)

    def transform_MEDPRICE(self):
        self.df['transform_MEDPRICE'] = MEDPRICE(self.high,self.low)

    def transform_TYPPRICE(self):
        self.df['transform_TYPPRICE'] = TYPPRICE(self.high,self.low,self.close)

    def transform_WCLPRICE(self):
        self.df['transform_WCLPRICE'] = WCLPRICE(self.high,self.low,self.close)

    def cycle_HT_DCPERIOD(self):
        self.df['cycle_HT_DCPERIOD'] = HT_DCPERIOD(self.close)

    def cycle_HT_DCPHASE(self):
        self.df['cycle_HT_DCPHASE'] = HT_DCPHASE(self.close)

    def cycle_HT_PHASOR(self):
        self.df['cycle_HT_PHASOR_inphase'],self.df['cycle_HT_PHASOR_quadrature'] = HT_PHASOR(self.close)

    def cycle_HT_SINE(self):
        self.df['cycle_HT_SINE'],self.df['cycle_HT_SINE_LEAD'] = HT_SINE(self.close)

    def cycle_HT_TRENDMODE(self):
        self.df['cycle_HT_TRENDMODE'] = HT_TRENDMODE(self.close)

    def pattern_2_crows(self):
        self.df['pattern_2_crows'] = CDL2CROWS(self.open,self.high,self.low,self.close)

    def pattern_3_black_crows(self):
        self.df['pattern_3_black_crows'] = CDL3BLACKCROWS(self.open,self.high,self.low,self.close)

    def pattern_3_inside_updown(self):
        self.df['pattern_3_inside_updown'] = CDL3INSIDE(self.open,self.high,self.low,self.close)

    def pattern_3_line_strike(self):
        self.df['pattern_3_line_strike'] = CDL3LINESTRIKE(self.open,self.high,self.low,self.close)

    def pattern_3_outside_updown(self):
        self.df['pattern_3_outside_updown'] = CDL3OUTSIDE(self.open,self.high,self.low,self.close)

    def pattern_3_stars_south(self):
        self.df['pattern_3_stars_south'] = CDL3STARSINSOUTH(self.open,self.high,self.low,self.close)

    def pattern_3_adv_white_soldier(self):
        self.df['pattern_3_adv_white_soldier'] = CDL3WHITESOLDIERS(self.open,self.high,self.low,self.close)

    def pattern_abondoned_baby(self,penetration=0):
        self.df['pattern_abondoned_baby'] = CDLABANDONEDBABY(self.open,self.high,self.low,self.close,penetration)

    def pattern_advance_block(self):
        self.df['pattern_advance_block'] = CDLADVANCEBLOCK(self.open,self.high,self.low,self.close)

    def pattern_belt_hold(self):
        self.df['pattern_belt_hold'] = CDLBELTHOLD(self.open,self.high,self.low,self.close)

    def pattern_breakaway(self):
        self.df['pattern_breakaway'] = CDLBREAKAWAY(self.open,self.high,self.low,self.close)

    def pattern_closing_marubozu(self):
        self.df['pattern_closing_marubozu'] = CDLCLOSINGMARUBOZU(self.open,self.high,self.low,self.close)

    def pattern_concealing_baby_swallow(self):
        self.df['pattern_concealing_baby_swallow '] = CDLCONCEALBABYSWALL(self.open,self.high,self.low,self.close)

    def pattern_counter_attack(self):
        self.df['pattern_counter_attack '] = CDLCOUNTERATTACK(self.open,self.high,self.low,self.close)

    def pattern_dark_cloud_cover(self,penetration=0):
        self.df['pattern_dark_cloud_cover '] = CDLDARKCLOUDCOVER(self.open,self.high,self.low,self.close,penetration)

    def pattern_doji(self):
        self.df['pattern_doji '] = CDLDOJI(self.open,self.high,self.low,self.close)

        
    def pattern_doji_star(self):
        self.df['pattern_doji_star '] = CDLDOJISTAR(self.open,self.high,self.low,self.close)

    def pattern_dragonfly_doji(self):
        self.df['pattern_dragonfly_doji '] = CDLDRAGONFLYDOJI(self.open,self.high,self.low,self.close)

    def pattern_engulfing_pattern(self):
        self.df['pattern_engulfing_pattern '] = CDLENGULFING(self.open,self.high,self.low,self.close) 

    def pattern_evening_doji_star(self):
        self.df['pattern_evening_doji_star'] = CDLEVENINGDOJISTAR(self.open,self.high,self.low,self.close) 

    def pattern_evening_star(self):
        self.df['pattern_evening_star'] = CDLEVENINGSTAR(self.open,self.high,self.low,self.close) 

    def pattern_updown_gapside_white_lines(self):
        self.df['pattern_updown_gapside_white_lines'] = CDLGAPSIDESIDEWHITE(self.open,self.high,self.low,self.close) 

    def pattern_gravestone_doji(self):
        self.df['pattern_gravestone_doji'] = CDLGRAVESTONEDOJI(self.open,self.high,self.low,self.close) 

    def pattern_hammer(self):
        self.df['pattern_hammer'] = CDLHAMMER(self.open,self.high,self.low,self.close) 

    def pattern_hanging_man(self):
        self.df['pattern_hanging_man'] = CDLHANGINGMAN(self.open,self.high,self.low,self.close) 

    def pattern_harami(self):
        self.df['pattern_harami'] = CDLHARAMI(self.open,self.high,self.low,self.close) 

    def pattern_harami_cross(self):
        self.df['pattern_harami_cross'] = CDLHARAMICROSS(self.open,self.high,self.low,self.close) 

    def pattern_high_wave_candle(self):
        self.df['pattern_high_wave_candle'] = CDLHIGHWAVE(self.open,self.high,self.low,self.close) 

    def pattern_hikkake(self):
        self.df['pattern_hikkake'] = CDLHIKKAKE(self.open,self.high,self.low,self.close) 

    def pattern_modified_hikkake(self):
        self.df['pattern_modified_hikkake'] = CDLHIKKAKEMOD(self.open,self.high,self.low,self.close) 

    def pattern_homing_pigeon(self):
        self.df['pattern_homing_pigeon'] = CDLHOMINGPIGEON(self.open,self.high,self.low,self.close) 

    def pattern_identical_3_cross(self):
        self.df['pattern_harami_cross'] = CDLIDENTICAL3CROWS(self.open,self.high,self.low,self.close) 

    def pattern_in_neck(self):
        self.df['pattern_in_neck'] = CDLINNECK(self.open,self.high,self.low,self.close) 

    def pattern_inverted_hammer(self):
        self.df['pattern_inverted_hammer'] = CDLINVERTEDHAMMER(self.open,self.high,self.low,self.close) 

    def pattern_kicking(self):
        self.df['pattern_kicking'] = CDLKICKING(self.open,self.high,self.low,self.close) 

    def pattern_kicking_bullbear_morubozu(self):
        self.df['pattern_kicking_bullbear_morubozu'] = CDLKICKINGBYLENGTH(self.open,self.high,self.low,self.close) 

    def pattern_ladder_bottom(self):
        self.df['pattern_ladder_bottom'] = CDLLADDERBOTTOM(self.open,self.high,self.low,self.close) 

    def pattern_long_leg_doji(self):
        self.df['pattern_long_leg_doji'] = CDLLONGLEGGEDDOJI(self.open,self.high,self.low,self.close)

    def pattern_long_line_candle(self):
        self.df['pattern_long_line_candle'] = CDLLONGLINE(self.open,self.high,self.low,self.close)

    def pattern_morubozu(self):
        self.df['pattern_morubozu'] = CDLMARUBOZU(self.open,self.high,self.low,self.close)

    def pattern_matching_low(self):
        self.df['pattern_matching_low'] = CDLMATCHINGLOW(self.open,self.high,self.low,self.close)

    def pattern_mat_holding(self):
        self.df['pattern_mat_holding'] = CDLMATHOLD(self.open,self.high,self.low,self.close)

    def pattern_morning_doji_star(self,penetration=0):
        self.df['pattern_morning_doji_star'] = CDLMORNINGDOJISTAR(self.open,self.high,self.low,self.close,penetration)

    def pattern_morning_star(self,penetration=0):
        self.df['pattern_morning_star'] = CDLMORNINGSTAR(self.open,self.high,self.low,self.close,penetration)

    def pattern_on_neck(self):
        self.df['pattern_on_neck'] = CDLONNECK(self.open,self.high,self.low,self.close)

    def pattern_piercing(self):
        self.df['pattern_piercing'] = CDLPIERCING(self.open,self.high,self.low,self.close)

    def pattern_rickshaw_man(self):
        self.df['pattern_rickshaw_man'] = CDLRICKSHAWMAN(self.open,self.high,self.low,self.close)

    def pattern_risefall_3_methods(self):
        self.df['pattern_rickshaw_man'] = CDLRISEFALL3METHODS(self.open,self.high,self.low,self.close)

    def pattern_separating_lines(self):
        self.df['pattern_separating_lines'] = CDLSEPARATINGLINES(self.open,self.high,self.low,self.close)

    def pattern_shooting_star(self):
        self.df['pattern_shooting_star'] = CDLSHOOTINGSTAR(self.open,self.high,self.low,self.close)

    def pattern_short_line(self):
        self.df['pattern_short_line'] = CDLSHORTLINE(self.open,self.high,self.low,self.close)

    def pattern_spinning_top(self):
        self.df['pattern_spinning_top'] = CDLSPINNINGTOP(self.open,self.high,self.low,self.close)

    def pattern_stalled(self):
        self.df['pattern_stalled'] = CDLSTALLEDPATTERN(self.open,self.high,self.low,self.close)

    def pattern_stick_sandwich(self):
        self.df['pattern_stick_sandwich'] = CDLSTICKSANDWICH(self.open,self.high,self.low,self.close)

    def pattern_takuri(self):
        self.df['pattern_takuri'] = CDLTAKURI(self.open,self.high,self.low,self.close)

    def pattern_tasuki_gap(self):
        self.df['pattern_tasuki_gap'] = CDLTASUKIGAP(self.open,self.high,self.low,self.close)

    def pattern_thrusting_pattern(self):
        self.df['pattern_thrusting_pattern'] = CDLTHRUSTING(self.open,self.high,self.low,self.close)

    def pattern_tristar_pattern(self):
        self.df['pattern_tristar_pattern'] = CDLTRISTAR(self.open,self.high,self.low,self.close)

    def pattern_unique_3_river(self):
        self.df['pattern_unique_3_river'] = CDLUNIQUE3RIVER(self.open,self.high,self.low,self.close)

    def pattern_upside_gap_2_crows(self):
        self.df['pattern_upside_gap_2_crows'] = CDLUPSIDEGAP2CROWS(self.open,self.high,self.low,self.close)

    def pattern_updown_gap_3_method(self):
        self.df['pattern_updown_gap_3_method'] = CDLUPSIDEGAP2CROWS(self.open,self.high,self.low,self.close)

    def stats_beta(self,timeperiod=5):
        self.df['stats_beta'] = BETA(self.high,self.low,timeperiod)

    def stats_pearson_coeff(self,timeperiod=30):
        self.df['stats_pearson_coeff'] = CORREL(self.high,self.low,timeperiod)

    def stats_linear_reg(self,timeperiod=14):
        self.df['stats_linear_reg'] = LINEARREG(self.close,timeperiod)

    def stats_linear_reg_angle(self,timeperiod=14):
        self.df['stats_linear_reg_angle'] = LINEARREG_ANGLE(self.close,timeperiod)

    def stats_linear_reg_intercept(self,timeperiod=14):
        self.df['stats_linear_reg_intercept'] = LINEARREG_INTERCEPT(self.close,timeperiod)

    def stats_linear_reg_slope(self,timeperiod=14):
        self.df['stats_linear_reg_slope'] = LINEARREG_SLOPE(self.close,timeperiod)

    def stats_linear_reg_slope(self,timeperiod=5, nbdev=1):
        self.df['stats_linear_reg_slope'] = STDDEV(self.close,timeperiod,nbdev)

    def stats_time_series_forecast(self,timeperiod=14):
        self.df['stats_linear_reg_slope'] = TSF(self.close,timeperiod)

    def stats_variance(self,timeperiod=5, nbdev=1):
        self.df['stats_variance'] = VAR(self.close,timeperiod,nbdev)

    def math_ACOS(self):
        self.df['math_ACOS'] = ACOS(self.close)

    def math_ASIN(self):
        self.df['math_ASIN'] = ASIN(self.close)

    def math_ATAN(self):
        self.df['math_ATAN'] = ATAN(self.close)

    def math_CEIL(self):
        self.df['math_CEIL'] = CEIL(self.close)

    def math_COS(self):
        self.df['math_COS'] = COS(self.close)

    def math_COSH(self):
        self.df['math_COSH'] = COSH(self.close)

    def math_EXP(self):
        self.df['math_EXP'] = EXP(self.close)
    
    def math_FLOOR(self):
        self.df['math_FLOOR'] = FLOOR(self.close)

    def math_LN(self):
        self.df['math_LN'] = LN(self.close)

    def math_LOG10(self):
        self.df['math_LOG10'] = LOG10(self.close)

    def math_SIN(self):
        self.df['math_SIN'] = SIN(self.close)

    def math_SINH(self):
        self.df['math_SINH'] = SINH(self.close)

    def math_SQRT(self):
        self.df['math_SQRT'] = SQRT(self.close)

    def math_TAN(self):
        self.df['math_TAN'] = TAN(self.close)

    def math_TANH(self):
        self.df['math_TANH'] = TANH(self.close)

    def overlap_bolliner_bands(self,timeperiod=5, nbdevup=2, nbdevdn=2, matype=0):
        self.df['overlap_bb_upper'],self.df['overlap_bb_middle'],self.df['overlap_bb_lower'] = BBANDS(self.close, timeperiod, nbdevup, nbdevdn, matype)

    def overlap_double_exp_moving_avg(self,timeperiod=30):
        self.df['overlap_double_exp_moving_avg'] = DEMA(self.close, timeperiod)

    def overlap_exp_moving_avg(self,timeperiod=30):
        self.df['overlap_exp_moving_avg'] = EMA(self.close, timeperiod)

    def overlap_hilbert_transform(self):
        self.df['overlap_hilbert_transform'] = HT_TRENDLINE(self.close)

    def overlap_kaufman_adaptive_moving_avg(self, timeperiod=30):
        self.df['overlap_kaufman_adaptive_moving_avg'] = KAMA(self.close,timeperiod)

    def overlap_moving_avg(self, timeperiod=30, matype=0):
        self.df['overlap_moving_avg'] = MA(self.close,timeperiod,matype)

    def overlap_mesa_adaptive_moving_average(self, fastlimit=0, slowlimit=0):
        self.df['overlap_mama'],self.df['overlap_fama'] = MAMA(self.close,fastlimit,slowlimit)

    def overlap_moving_avg_with_variable(self,periods, minperiod=2, maxperiod=30, matype=0):
        self.df['overlap_moving_avg_with_variable'] = MAVP(self.close,periods, minperiod, maxperiod, matype)

    def overlap_midpoint(self, timeperiod=14):
        self.df['overlap_midpoint'] = MIDPOINT(self.close,timeperiod)

    def overlap_midpoint_price(self, timeperiod=14):
        self.df['overlap_midpoint_price'] = MIDPRICE(self.high,self.low,timeperiod)

    def overlap_parabolic_sar(self, acceleration=0, maximum=0):
        self.df['overlap_parabolic_sar'] = SAR(self.high,self.low,acceleration,maximum)

    def overlap_parabolic_sar_ext(self, startvalue=0, offsetonreverse=0, accelerationinitlong=0, accelerationlong=0, accelerationmaxlong=0, accelerationinitshort=0, accelerationshort=0, accelerationmaxshort=0):
        self.df['overlap_parabolic_sar_ext'] = SAREXT(self.high,self.low,startvalue, offsetonreverse, accelerationinitlong, accelerationlong, accelerationmaxlong, accelerationinitshort, accelerationshort, accelerationmaxshort)

    def overlap_simple_moving_avg(self, timeperiod=30):
        self.df['overlap_simple_moving_avg'] = SMA(self.close,timeperiod)

    def overlap_triple_exp_moving_average_t3(self, timeperiod=5,vfactor=0):
        self.df['overlap_triple_exp_moving_average_t3'] = T3(self.close,timeperiod,vfactor)

    def overlap_triangular_moving_average(self, timeperiod=30):
        self.df['overlap_triangular_moving_average'] = TRIMA(self.close,timeperiod)

    def overlap_weighted_moving_average(self, timeperiod=30):
        self.df['overlap_weighted_moving_average'] = WMA(self.close,timeperiod)

    

