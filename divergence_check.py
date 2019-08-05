#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug  4 17:14:03 2019

@author: dpong
"""

import pandas as pd
import numpy as np
import pandas_datareader as pdr
from talib import abstract


class Divergence_test():
    def __init__(self,n=20):   
        self.df = pd.DataFrame()
        self.monitor_days = n
        
    def get_data(self,ticker):
        #取得資料和RSI,要先整理成Talib接受的小寫格式...
        self.df = pdr.DataReader(ticker,'yahoo')
        self.df.drop(columns=['Adj Close'],inplace=True)
        self.df.rename(columns={'Open':'open',
                                'High':'high',
                                'Low':'low',
                                'Close':'close',
                                'Volume':'volume'},inplace=True)
        self.df['RSI'] = abstract.RSI(self.df)   
        self.df['OBV'] = abstract.OBV(self.df)
        self.df['short_ma'] = self.df['close'].rolling(window=5).mean()
        self.df['mid_ma'] = self.df['close'].rolling(window=10).mean()
        self.df['long_ma'] = self.df['close'].rolling(window=self.monitor_days).mean()
        self.df.dropna(inplace=True)              #drop掉nan的部分
        
        #因為是RSI，所以把收盤價以外的drop掉
        self.df_analysis = self.df.drop(columns=['open','high','low','volume']) 
        self.df_analysis['RSI_check'] = np.nan
        self.df_analysis['OBV_check'] = np.nan
        self.df_analysis['both_check'] = np.nan
        self.df_analysis['direction'] = np.nan
        self.df_analysis['direction_switch'] = np.nan
    
        
    def analysis(self):
        #分析的部分都以numpy來做，加速運算
        data = np.array(self.df_analysis)
        #起始
        highest_close = data[0][0]
        highest_rsi = data[0][1]
        highest_obv = data[0][2]
        lowest_close = data[0][0]
        lowest_rsi = data[0][1]
        lowest_obv = data[0][2]
        days = 0
        #均線順排列定義成趨勢，其餘定義成盤整
        for i in range(1,data.shape[0]):
                 
            if data[i][3] > data[i][4] and data[i][4] > data[i][5]:  #判斷為漲勢
                data[i][9] = 100  #設定+100為漲勢
                if data[i][0] > highest_close:
                    highest_close = data[i][0]   #創新高，紀錄
                    if data[i][1] > highest_rsi:
                        highest_rsi = data[i][1]
                    else:
                        data[i][6] = 10  #RSI漲勢背離，設定為+10
                    if data[i][2] > highest_obv:
                        highest_obv = data[i][2]
                    else:
                        data[i][7] = 10  #obv漲勢背離，設定為+10
                    if data[i][6] == 10 and data[i][7] == 10:  #兩指標都背離，紀錄為+10
                        data[i][8] = 10
        
            elif data[i][3] < data[i][4] and data[i][4] < data[i][5]: #判斷為跌勢
                data[i][9] = -100  #設定-100為跌勢
                if data[i][0] < lowest_close:
                    lowest_close = data[i][0]   #創新低，紀錄
                    if data[i][1] < lowest_rsi:
                        lowest_rsi = data[i][1]
                    else:
                        data[i][6] = -10  #RSI跌勢背離，設定為-10
                    if data[i][2] < lowest_obv:
                        lowest_obv = data[i][2]
                    else:
                        data[i][7] = -10  #obv跌勢背離，設定為-10
                    if data[i][6] == -10 and data[i][7] == -10:  #兩指標都背離，紀錄為-10
                        data[i][8] = -10
                
            else:
                data[i][9] = 0      #設定0為盤整，紀錄資料洗牌成當日資料
                highest_close = data[i][0]
                highest_rsi = data[i][1]
                highest_obv = data[i][2]
                lowest_close = data[i][0]
                lowest_rsi = data[i][1]
                lowest_obv = data[i][2]
                
            if not data[i][9] == data[i-1][9]:   #狀態改變設定為1，方便判斷
                data[i][10] = 1
                    
            #放回dataframe，方便查看
            self.df_analysis = pd.DataFrame(index=self.df_analysis.index,
                                            data=data,
                                           columns=self.df_analysis.columns)
    def result(self):
        #結果檢驗
        test_list = ['RSI_check','OBV_check','both_check']
        
        for x in test_list:
            self.df_check = self.df_analysis[[x,'direction_switch']]
            self.df_check = self.df_check.dropna(how='all')
        
            divergence = 0
            count_diver = np.array([])
            count_switch = np.array([])
            for i in range(self.df_check.shape[0]):
                if not np.isnan(self.df_check.iloc[i,0]) and divergence == 0:
                    divergence = 1
                    count_diver = np.append(count_diver,self.df_check.iloc[i].name)
                if divergence == 1 and self.df_check.iloc[i,1] == 1:
                    divergence = 0
                    count_switch = np.append(count_switch,self.df_check.iloc[i].name) 
                    
            result = np.array([])
            for i in range(len(count_diver)):
                diff = count_switch[i]-count_diver[i]
                result = np.append(result,diff.days)
            
            print('Type: ',x)
            print('mean: ',round(result[result<self.monitor_days].mean(),2),'days')
            print('std : ',round(result[result<self.monitor_days].std(),2),'days')
            print('-'*80) 
    


if __name__ == '__main__':
   d = Divergence_test()
   d.get_data('^TWII')
   d.analysis()
   d.result()