import pandas as pd
import numpy as np
import time
import json
import akshare as ak

# 计算BOLL指标
def calculate_boll(data, window=20, num_std=2):
    data['MA'] = data['close'].rolling(window=window).mean()
    data['STD'] = data['close'].rolling(window=window).std()
    data['upper'] = data['MA'] + (data['STD'] * num_std)
    data['lower'] = data['MA'] - (data['STD'] * num_std)
    return data

# 获取历史数据（优先使用AkShare，失败时使用模拟数据）
def get_history_data(symbol="000333", period="1d", limit=365):
    try:
        # 计算开始日期
        end_date = pd.Timestamp.now().strftime("%Y%m%d")
        start_date = (pd.Timestamp.now() - pd.Timedelta(days=limit)).strftime("%Y%m%d")
        
        # 使用AkShare获取A股历史数据
        print(f"正在使用AkShare获取{symbol}的历史数据...")
        df = ak.stock_zh_a_hist(
            symbol=symbol, 
            period="daily", 
            start_date=start_date, 
            end_date=end_date, 
            adjust="qfq"  # 前复权
        )
        
        # 重命名列以匹配现有函数的期望格式
        df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '最高': 'high',
            '最低': 'low',
            '收盘': 'close',
            '成交量': 'volume'
        }, inplace=True)
        
        # 确保date列是datetime类型
        df['date'] = pd.to_datetime(df['date'])
        
        print(f"成功获取{len(df)}条历史数据")
        return df
    except Exception as e:
        print(f"获取真实数据失败: {e}")
        print("使用模拟数据作为备选方案")
        
        # 生成模拟数据
        dates = pd.date_range(start=pd.Timestamp.now() - pd.Timedelta(days=limit), end=pd.Timestamp.now(), freq='D')
        close = np.random.normal(50, 5, size=len(dates))
        high = close * (1 + np.random.uniform(0, 0.05, size=len(dates)))
        low = close * (1 - np.random.uniform(0, 0.05, size=len(dates)))
        open = close * (1 + np.random.uniform(-0.02, 0.02, size=len(dates)))
        
        df = pd.DataFrame({
            'date': dates,
            'open': open,
            'high': high,
            'low': low,
            'close': close,
            'volume': np.random.normal(1000000, 500000, size=len(dates))
        })
        
        print(f"生成{len(df)}条模拟数据")
        return df

# 分析BOLL突破情况
def analyze_boll_breakouts(df):
    df = calculate_boll(df)
    breakouts = {
        "above_upper": 0,
        "below_lower": 0,
        "total_days": len(df)
    }
    
    for i in range(1, len(df)):
        # 检查开盘后最高价是否突破BOLL上轨
        if df.loc[i, 'high'] > df.loc[i, 'upper']:
            breakouts["above_upper"] += 1
        # 检查开盘后最低价是否突破BOLL下轨
        if df.loc[i, 'low'] < df.loc[i, 'lower']:
            breakouts["below_lower"] += 1
    
    # 计算突破比例
    breakouts["above_upper_ratio"] = breakouts["above_upper"] / breakouts["total_days"] * 100
    breakouts["below_lower_ratio"] = breakouts["below_lower"] / breakouts["total_days"] * 100
    
    return breakouts

# 实时行情监控（模拟）
def monitor_realtime(duration=10):
    print("开始实时行情监控...")
    start_time = time.time()
    
    while time.time() - start_time < duration:
        # 模拟实时价格数据
        price = round(50 + np.random.normal(0, 1), 2)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(f"实时价格: {price} 时间: {timestamp}")
        time.sleep(1)  # 每秒更新一次

def main():
    # 获取历史数据
    print("获取历史数据...")
    df = get_history_data()
    
    # 分析BOLL突破情况
    print("分析BOLL突破情况...")
    breakouts = analyze_boll_breakouts(df)
    
    # 输出分析结果
    print("\nBOLL指标分析结果（一年）:")
    print(f"总天数: {breakouts['total_days']}")
    print(f"突破上轨次数: {breakouts['above_upper']} ({breakouts['above_upper_ratio']:.2f}%)")
    print(f"突破下轨次数: {breakouts['below_lower']} ({breakouts['below_lower_ratio']:.2f}%)")
    
    # 保存分析结果到文件
    with open('midea_boll_analysis.json', 'w') as f:
        json.dump(breakouts, f, indent=2)
    print("\n分析结果已保存到 midea_boll_analysis.json 文件")
    
    # 开始实时监控
    print("\n开始实时监控（持续10秒）...")
    monitor_realtime()
    
    print("\n监控结束")

if __name__ == '__main__':
    main()