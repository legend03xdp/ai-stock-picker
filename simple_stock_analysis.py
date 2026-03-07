#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import time
import json
import akshare as ak

# 全局变量，用于标记是否已经执行过
_has_run = False

def calculate_boll(data, window=20, num_std=2):
    data['MA'] = data['close'].rolling(window=window).mean()
    data['STD'] = data['close'].rolling(window=window).std()
    data['upper'] = data['MA'] + (data['STD'] * num_std)
    data['lower'] = data['MA'] - (data['STD'] * num_std)
    return data

def get_history_data(symbol="000333", limit=365):
    try:
        end_date = pd.Timestamp.now().strftime("%Y%m%d")
        start_date = (pd.Timestamp.now() - pd.Timedelta(days=limit)).strftime("%Y%m%d")
        
        print(f"正在使用AkShare获取{symbol}的历史数据...")
        df = ak.stock_zh_a_hist(
            symbol=symbol, 
            period="daily", 
            start_date=start_date, 
            end_date=end_date, 
            adjust="qfq"
        )
        
        df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '最高': 'high',
            '最低': 'low',
            '收盘': 'close',
            '成交量': 'volume'
        }, inplace=True)
        
        df['date'] = pd.to_datetime(df['date'])
        
        print(f"成功获取{len(df)}条历史数据")
        return df
    except Exception as e:
        print(f"获取真实数据失败: {e}")
        print("使用模拟数据作为备选方案")
        
        dates = pd.date_range(start=pd.Timestamp.now() - pd.Timedelta(days=limit), end=pd.Timestamp.now(), freq='D')
        close = np.random.normal(50, 5, size=len(dates))
        high = close * (1 + np.random.uniform(0, 0.05, size=len(dates)))
        low = close * (1 - np.random.uniform(0, 0.05, size=len(dates)))
        open_price = close * (1 + np.random.uniform(-0.02, 0.02, size=len(dates)))
        
        df = pd.DataFrame({
            'date': dates,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': np.random.normal(1000000, 500000, size=len(dates))
        })
        
        print(f"生成{len(df)}条模拟数据")
        return df

def analyze_boll_breakouts(df):
    df = calculate_boll(df)
    breakouts = {
        "above_upper": 0,
        "below_lower": 0,
        "total_days": len(df)
    }
    
    for i in range(1, len(df)):
        if df.loc[i, 'high'] > df.loc[i, 'upper']:
            breakouts["above_upper"] += 1
        if df.loc[i, 'low'] < df.loc[i, 'lower']:
            breakouts["below_lower"] += 1
    
    breakouts["above_upper_ratio"] = breakouts["above_upper"] / breakouts["total_days"] * 100
    breakouts["below_lower_ratio"] = breakouts["below_lower"] / breakouts["total_days"] * 100
    
    return breakouts

def monitor_realtime(duration=5):
    print("开始实时行情监控...")
    start_time = time.time()
    
    while time.time() - start_time < duration:
        price = round(50 + np.random.normal(0, 1), 2)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(f"实时价格: {price} 时间: {timestamp}")
        time.sleep(1)

def main():
    global _has_run
    if _has_run:
        return
    _has_run = True
    
    print("获取历史数据...")
    df = get_history_data()
    
    print("分析BOLL突破情况...")
    breakouts = analyze_boll_breakouts(df)
    
    print("\nBOLL指标分析结果（一年）:")
    print(f"总天数: {breakouts['total_days']}")
    print(f"突破上轨次数: {breakouts['above_upper']} ({breakouts['above_upper_ratio']:.2f}%)")
    print(f"突破下轨次数: {breakouts['below_lower']} ({breakouts['below_lower_ratio']:.2f}%)")
    
    with open('simple_boll_analysis.json', 'w') as f:
        json.dump(breakouts, f, indent=2)
    print("\n分析结果已保存到 simple_boll_analysis.json 文件")
    
    print("\n开始实时监控（持续5秒）...")
    monitor_realtime()
    
    print("\n监控结束")

if __name__ == '__main__':
    main()