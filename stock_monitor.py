import requests
import pandas as pd
import numpy as np
import time
import json
from flask import Flask, render_template, jsonify, request
import threading

app = Flask(__name__)

# 全局变量
stock_data = {}
monitor_results = {}

# 计算BOLL指标
def calculate_boll(data, window=20, num_std=2):
    data['MA'] = data['close'].rolling(window=window).mean()
    data['STD'] = data['close'].rolling(window=window).std()
    data['upper'] = data['MA'] + (data['STD'] * num_std)
    data['lower'] = data['MA'] - (data['STD'] * num_std)
    return data

# 获取A股历史数据（只使用真实API，失败时抛出异常）
def get_history_data(symbol="000333", start_date=None, end_date=None):
    # 处理日期参数
    if not end_date:
        end_date = pd.Timestamp.now()
    else:
        # 处理字符串格式的日期
        if isinstance(end_date, str):
            # 尝试不同的日期格式
            try:
                if len(end_date) == 8:  # YYYYMMDD格式
                    end_date = pd.to_datetime(end_date, format='%Y%m%d')
                else:  # YYYY-MM-DD格式
                    end_date = pd.to_datetime(end_date)
            except:
                raise ValueError("结束日期格式错误，请使用YYYYMMDD或YYYY-MM-DD格式")
    
    if not start_date:
        start_date = pd.Timestamp.now() - pd.Timedelta(days=365)
    else:
        # 处理字符串格式的日期
        if isinstance(start_date, str):
            # 尝试不同的日期格式
            try:
                if len(start_date) == 8:  # YYYYMMDD格式
                    start_date = pd.to_datetime(start_date, format='%Y%m%d')
                else:  # YYYY-MM-DD格式
                    start_date = pd.to_datetime(start_date)
            except:
                raise ValueError("开始日期格式错误，请使用YYYYMMDD或YYYY-MM-DD格式")
    
    print(f"正在获取{symbol}的历史数据...")
    
    # 使用新浪财经API获取真实历史数据
    url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
    params = {
        "symbol": f"sz{symbol}",
        "scale": 240,  # 240分钟，即日线
        "ma": 5,      # 5日均线
        "datalen": 365  # 数据长度，365天
    }
    
    # 添加请求头，模拟浏览器请求
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://money.finance.sina.com.cn/"
    }
    
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    
    # 解析JSON数据
    data = response.json()
    
    if not data:
        raise ValueError("未获取到历史数据")
    
    dates = []
    open_prices = []
    high_prices = []
    low_prices = []
    close_prices = []
    volumes = []
    
    for item in data:
        try:
            dates.append(pd.to_datetime(item['day']))
            open_prices.append(float(item['open']))
            high_prices.append(float(item['high']))
            low_prices.append(float(item['low']))
            close_prices.append(float(item['close']))
            volumes.append(float(item['volume']))
        except:
            # 跳过数据格式错误的行
            continue
    
    # 构建DataFrame
    df = pd.DataFrame({
        'open_time': dates,
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': volumes
    })
    
    # 按日期排序
    df.sort_values('open_time', inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    if df.empty:
        raise ValueError("解析历史数据失败")
    
    print(f"成功获取{len(df)}条真实历史数据")
    return df

# 分析BOLL突破情况
def analyze_boll_breakouts(df):
    df = calculate_boll(df)
    breakouts = {
        "above_upper": 0,
        "below_lower": 0,
        "total_days": len(df),
        "breakout_data": []  # 只存储突破的明细
    }
    
    for i in range(len(df)):
        # 检查是否突破
        if i > 0:
            above_upper = False
            below_lower = False
            breakout_percentage = 0
            
            if df.loc[i, 'high'] > df.loc[i, 'upper']:
                breakouts["above_upper"] += 1
                above_upper = True
                # 计算突破百分比：(最高价 - 上轨) / 上轨 * 100
                breakout_percentage = (float(df.loc[i, 'high']) - float(df.loc[i, 'upper'])) / float(df.loc[i, 'upper']) * 100
            if df.loc[i, 'low'] < df.loc[i, 'lower']:
                breakouts["below_lower"] += 1
                below_lower = True
                # 计算突破百分比：(下轨 - 最低价) / 下轨 * 100
                breakout_percentage = (float(df.loc[i, 'lower']) - float(df.loc[i, 'low'])) / float(df.loc[i, 'lower']) * 100
            
            # 只添加有突破的日期数据
            if above_upper or below_lower:
                day_data = {
                    "date": df.loc[i, 'open_time'].strftime("%Y-%m-%d"),
                    "open": round(float(df.loc[i, 'open']), 2),
                    "high": round(float(df.loc[i, 'high']), 2),
                    "low": round(float(df.loc[i, 'low']), 2),
                    "close": round(float(df.loc[i, 'close']), 2),
                    "volume": round(float(df.loc[i, 'volume']), 0),
                    "MA": round(float(df.loc[i, 'MA']), 2) if not pd.isna(df.loc[i, 'MA']) else None,
                    "upper": round(float(df.loc[i, 'upper']), 2) if not pd.isna(df.loc[i, 'upper']) else None,
                    "lower": round(float(df.loc[i, 'lower']), 2) if not pd.isna(df.loc[i, 'lower']) else None,
                    "above_upper": above_upper,
                    "below_lower": below_lower,
                    "breakout_percentage": round(breakout_percentage, 2)  # 增加突破百分比
                }
                breakouts["breakout_data"].append(day_data)
    
    # 计算突破比例
    if breakouts["total_days"] > 0:
        breakouts["above_upper_ratio"] = breakouts["above_upper"] / breakouts["total_days"] * 100
        breakouts["below_lower_ratio"] = breakouts["below_lower"] / breakouts["total_days"] * 100
    else:
        breakouts["above_upper_ratio"] = 0
        breakouts["below_lower_ratio"] = 0
    
    # 添加模拟交易结果
    breakouts["simulation_result"] = simulate_trading(df)
    
    return breakouts

# 模拟交易模块
def simulate_trading(df):
    # 初始净值
    initial_net_value = 1.0
    
    # 策略1：买入后一直持有
    buy_and_hold = []
    current_net_value = initial_net_value
    initial_price = float(df.loc[0, 'close'])
    
    for i in range(len(df)):
        current_price = float(df.loc[i, 'close'])
        # 计算净值（含股息分红，这里简化为价格变化）
        net_value = initial_net_value * (current_price / initial_price)
        buy_and_hold.append({
            "date": df.loc[i, 'open_time'].strftime("%Y-%m-%d"),
            "net_value": round(net_value, 4)
        })
    
    # 策略2：突破上轨卖出，突破下轨买入
    boll_strategy = []
    current_net_value = initial_net_value
    position = True  # 初始状态为持有，按开始日期收盘价买入
    buy_price = float(df.loc[0, 'close'])  # 开始日期的收盘价作为初始买入价格
    buy_signals = []  # 买入信号
    sell_signals = []  # 卖出信号
    
    # 添加初始买入信号
    buy_signals.append({
        "date": df.loc[0, 'open_time'].strftime("%Y-%m-%d"),
        "price": buy_price
    })
    
    for i in range(len(df)):
        action = None
        if i == 0:
            # 初始日期，已经买入
            action = "buy"
        elif i > 0:
            # 检查是否突破上轨，持有状态下卖出
            if float(df.loc[i, 'high']) > float(df.loc[i, 'upper']) and position:
                # 卖出，按收盘价计算
                sell_price = float(df.loc[i, 'close'])
                current_net_value *= (sell_price / buy_price)
                position = False
                action = "sell"
                sell_signals.append({
                    "date": df.loc[i, 'open_time'].strftime("%Y-%m-%d"),
                    "price": sell_price
                })
            # 检查是否突破下轨，空仓时买入
            elif float(df.loc[i, 'low']) < float(df.loc[i, 'lower']) and not position:
                # 买入，按收盘价计算
                buy_price = float(df.loc[i, 'close'])
                position = True
                action = "buy"
                buy_signals.append({
                    "date": df.loc[i, 'open_time'].strftime("%Y-%m-%d"),
                    "price": buy_price
                })
        
        # 计算当前净值
        if position:
            current_price = float(df.loc[i, 'close'])
            # 计算当前净值：基于买入价格的变化
            net_value = current_net_value * (current_price / buy_price)
        else:
            # 空仓时净值保持不变
            net_value = current_net_value
        boll_strategy.append({
            "date": df.loc[i, 'open_time'].strftime("%Y-%m-%d"),
            "net_value": round(net_value, 4),
            "position": position,
            "action": action
        })
        
        # 更新当前净值，用于下一次计算
        current_net_value = net_value
    
    # 提取股价数据用于前端对比
    stock_prices = []
    for i in range(len(df)):
        stock_prices.append({
            "date": df.loc[i, 'open_time'].strftime("%Y-%m-%d"),
            "price": round(float(df.loc[i, 'close']), 2)
        })
    
    return {
        "buy_and_hold": buy_and_hold,
        "boll_strategy": boll_strategy,
        "stock_prices": stock_prices,
        "buy_signals": buy_signals,
        "sell_signals": sell_signals
    }

# 获取实时行情（使用腾讯财经API获取真实数据）
def get_realtime_price():
    global stock_data
    
    # 使用腾讯财经API获取实时价格数据
    print("正在获取实时价格数据...")
    
    # 构建腾讯财经API URL
    # 腾讯财经实时数据API
    url = "http://qt.gtimg.cn/q"
    params = {
        "q": "sz000333"
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # 检查请求是否成功
        
        # 解析数据
        content = response.text
        data = content.split('~')
        
        if len(data) >= 4:
            price = data[3]  # 最新价
            if price and price != '0':
                stock_data = {
                    "symbol": "000333",
                    "price": round(float(price), 2),
                    "timestamp": int(time.time() * 1000)
                }
                print(f"获取到实时价格: {price}")
            else:
                # 获取失败时直接显示失败信息
                stock_data = {
                    "symbol": "000333",
                    "price": None,
                    "error": "获取实时数据失败: 价格数据为空",
                    "timestamp": int(time.time() * 1000)
                }
                print("获取实时数据失败: 价格数据为空")
        else:
            # 获取失败时直接显示失败信息
            stock_data = {
                "symbol": "000333",
                "price": None,
                "error": "获取实时数据失败: 数据格式错误",
                "timestamp": int(time.time() * 1000)
            }
            print("获取实时数据失败: 数据格式错误")
    except Exception as e:
        # 获取失败时直接显示失败信息
        stock_data = {
            "symbol": "000333",
            "price": None,
            "error": f"获取实时数据失败: {str(e)}",
            "timestamp": int(time.time() * 1000)
        }
        print(f"获取实时数据失败: {e}")

# 启动监控线程
def start_monitoring():
    global monitor_results
    
    try:
        # 获取历史数据（默认一年）
        df = get_history_data()
        # 分析BOLL突破情况
        monitor_results = analyze_boll_breakouts(df)
    except Exception as e:
        print(f"启动监控失败: {e}")
        monitor_results = {"error": f"获取历史数据失败: {str(e)}"}
    
    # 初始化时获取一次实时价格
    get_realtime_price()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stock')
def get_stock_data():
    # 每次请求都获取最新的价格数据
    get_realtime_price()
    return jsonify(stock_data)

@app.route('/api/analysis')
def get_analysis():
    # 接收前端传递的日期范围参数
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 如果提供了日期范围，重新获取数据并分析
    if start_date and end_date:
        try:
            # 直接传递日期字符串，get_history_data函数会处理格式
            df = get_history_data(start_date=start_date, end_date=end_date)
            # 分析BOLL突破情况
            results = analyze_boll_breakouts(df)
            return jsonify(results)
        except Exception as e:
            return jsonify({"error": f"获取历史数据失败: {str(e)}"})
    
    # 默认返回当前结果
    return jsonify(monitor_results)

if __name__ == '__main__':
    # 启动监控
    start_monitoring()
    print("监控线程已启动")
    # 启动Flask应用
    print("启动Flask应用...")
    app.run(debug=False, host='0.0.0.0', port=8888)