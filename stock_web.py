#!/usr/bin/env python3
"""
巴菲特风格选股器 - Web可视化版
Buffett-Munger Stock Picker - Web UI
"""

from flask import Flask, render_template_string, jsonify, request
import urllib.request
import json
import ssl
from datetime import datetime

app = Flask(__name__)

# 禁用SSL警告
ssl._create_default_https_context = ssl._create_unverified_context

# A股关注列表
WATCHLIST = {
    "600519": {"name": "贵州茅台", "sector": "白酒"},
    "000333": {"name": "美的集团", "sector": "家电"},
    "600036": {"name": "招商银行", "sector": "银行"},
    "601318": {"name": "中国平安", "sector": "保险"},
    "002415": {"name": "海康威视", "sector": "安防"},
    "000858": {"name": "五粮液", "sector": "白酒"},
    "300750": {"name": "宁德时代", "sector": "新能源"},
    "600276": {"name": "恒瑞医药", "sector": "医药"},
    "002594": {"name": "比亚迪", "sector": "新能源车"},
    "600309": {"name": "万华化学", "sector": "化工"},
}

def get_stock_data(code: str) -> dict:
    """获取单只股票数据"""
    try:
        secid = f"1.{code}" if code.startswith("6") else f"0.{code}"
        url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f44,f45,f57,f58,f84,f85,f116,f117,f127,f128,f162,f163,f164,f167,f168,f169,f170,f173,f177,f178,f187,f188,f189,f190,f191,f192"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        if data.get("data"):
            d = data["data"]
            info = WATCHLIST.get(code, {"name": code, "sector": "未知"})
            
            # 价格
            price = d.get("f43", 0) / 1000 if d.get("f43") else 0
            change = d.get("f44", 0) / 100 if d.get("f44") else 0
            change_pct = d.get("f45", 0) / 100 if d.get("f45") else 0
            
            # 估值
            pe = d.get("f162", 0)  # 市盈率
            pb = d.get("f167", 0)  # 市净率
            
            # 盈利
            roe = d.get("f173", 0) if d.get("f173") else 0
            net_margin = d.get("f170", 0) if d.get("f170") else 0
            
            # 成长
            revenue_growth = d.get("f184", 0) if d.get("f184") else 0
            profit_growth = d.get("f190", 0) if d.get("f190") else 0
            
            # 计算评分
            score = calculate_score(roe, net_margin, pe, pb, profit_growth)
            
            return {
                "code": code,
                "name": info["name"],
                "sector": info["sector"],
                "price": price,
                "change": change,
                "change_pct": change_pct,
                "pe": pe,
                "pb": pb,
                "roe": roe,
                "net_margin": net_margin,
                "revenue_growth": revenue_growth,
                "profit_growth": profit_growth,
                "score": score,
                "status": "ok"
            }
    except Exception as e:
        return {"code": code, "status": "error", "message": str(e)}
    
    return {"code": code, "status": "error", "message": "No data"}

def calculate_score(roe, net_margin, pe, pb, profit_growth):
    """计算巴菲特风格评分"""
    score = 0
    
    # ROE (30分)
    if roe >= 20: score += 30
    elif roe >= 15: score += 25
    elif roe >= 12: score += 20
    elif roe >= 10: score += 15
    else: score += 5
    
    # 净利润率 (20分)
    if net_margin >= 20: score += 20
    elif net_margin >= 15: score += 15
    elif net_margin >= 10: score += 10
    elif net_margin >= 5: score += 5
    
    # 估值 (25分)
    if 0 < pe <= 15: score += 15
    elif pe <= 25: score += 10
    elif pe <= 35: score += 5
    
    if 0 < pb <= 2: score += 10
    elif pb <= 3: score += 7
    elif pb <= 5: score += 3
    
    # 成长性 (25分)
    if profit_growth >= 20: score += 15
    elif profit_growth >= 10: score += 10
    elif profit_growth >= 0: score += 5
    
    return score

# HTML模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>巴菲特风格选股器</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 30px;
        }
        h1 { font-size: 2.5rem; margin-bottom: 10px; }
        .subtitle { color: #888; font-size: 1rem; }
        .stats {
            display: flex;
            justify-content: center;
            gap: 40px;
            margin: 20px 0;
        }
        .stat-item { text-align: center; }
        .stat-value { font-size: 2rem; font-weight: bold; color: #4ade80; }
        .stat-label { color: #888; font-size: 0.9rem; }
        
        .controls {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        .search-box {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        .search-input {
            padding: 12px 20px;
            border: 2px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            background: rgba(255,255,255,0.1);
            color: #fff;
            font-size: 1rem;
            width: 250px;
            outline: none;
            transition: all 0.3s;
        }
        .search-input:focus {
            border-color: #4ade80;
            background: rgba(255,255,255,0.15);
        }
        .search-input::placeholder { color: #666; }
        
        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn-primary {
            background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
            color: #000;
            font-weight: bold;
        }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(74,222,128,0.4); }
        
        .btn-secondary {
            background: rgba(255,255,255,0.1);
            color: #fff;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .btn-secondary:hover { background: rgba(255,255,255,0.2); }
        
        .watchlist-section {
            margin-bottom: 30px;
        }
        .section-title {
            font-size: 1.2rem;
            margin-bottom: 15px;
            color: #888;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .stock-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
        }
        .stock-card {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.3s;
        }
        .stock-card:hover { transform: translateY(-5px); border-color: rgba(74,222,128,0.3); }
        
        .stock-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
        }
        .stock-name { font-size: 1.3rem; font-weight: bold; }
        .stock-code { color: #666; font-size: 0.9rem; }
        
        .score-badge {
            background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
            color: #000;
            padding: 8px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 1.2rem;
        }
        .score-low { background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); }
        .score-mid { background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%); }
        
        .price-section {
            display: flex;
            align-items: baseline;
            gap: 10px;
            margin: 15px 0;
        }
        .price { font-size: 2rem; font-weight: bold; }
        .change { font-size: 1rem; }
        .change-up { color: #ef4444; }
        .change-down { color: #22c55e; }
        
        .metrics {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-top: 15px;
        }
        .metric {
            background: rgba(0,0,0,0.2);
            padding: 10px;
            border-radius: 8px;
        }
        .metric-label { color: #888; font-size: 0.8rem; }
        .metric-value { font-size: 1.1rem; font-weight: bold; margin-top: 3px; }
        
        .loading {
            text-align: center;
            padding: 50px;
            color: #888;
        }
        .loading::after {
            content: "...";
            animation: dots 1.5s steps(4, end) infinite;
        }
        @keyframes dots {
            0%, 20% { content: "."; }
            40% { content: ".."; }
            60%, 100% { content: "..."; }
        }
        
        .sector-tag {
            display: inline-block;
            background: rgba(74,222,128,0.2);
            color: #4ade80;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.8rem;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📈 巴菲特风格选股器</h1>
            <p class="subtitle">价值投资 · 真实数据 · 双API校验</p>
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-value" id="totalStocks">-</div>
                    <div class="stat-label">股票数量</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="avgScore">-</div>
                    <div class="stat-label">平均评分</div>
                </div>
            </div>
        </header>
        
        <div class="controls">
            <div class="search-box">
                <input type="text" class="search-input" id="searchInput" placeholder="输入股票代码或名称 (如: 600519)" onkeypress="handleSearch(event)">
                <button class="btn btn-primary" onclick="searchStock()">🔍 查询</button>
            </div>
            <button class="btn btn-secondary" onclick="showWatchlist()">📋 关注列表</button>
            <button class="btn btn-primary" onclick="loadStocks()">🔄 刷新数据</button>
        </div>
        
        <div id="searchResult" class="stock-grid"></div>
        
        <div id="watchlistSection" class="watchlist-section">
            <div class="section-title">⭐ 关注列表</div>
            <div id="watchlistGrid" class="stock-grid"></div>
        </div>
    </div>
    
    <script>
        async function loadStocks() {
            const grid = document.getElementById('stockGrid');
            grid.innerHTML = '<div class="loading">正在获取数据...</div>';
            
            try {
                const response = await fetch('/api/stocks');
                const data = await response.json();
                
                if (data.error) {
                    grid.innerHTML = '<div class="loading">⚠️ ' + data.error + '</div>';
                    return;
                }
                
                const stocks = data.stocks || [];
                
                // 更新统计
                document.getElementById('totalStocks').textContent = stocks.length;
                const avgScore = stocks.length ? Math.round(stocks.reduce((a,b) => a + b.score, 0) / stocks.length) : 0;
                document.getElementById('avgScore').textContent = avgScore;
                
                // 排序
                stocks.sort((a, b) => b.score - a.score);
                
                // 渲染卡片
                grid.innerHTML = stocks.map((stock, idx) => {
                    const scoreClass = stock.score >= 70 ? '' : (stock.score >= 50 ? 'score-mid' : 'score-low');
                    const changeClass = stock.change >= 0 ? 'change-up' : 'change-down';
                    const changeSign = stock.change >= 0 ? '+' : '';
                    
                    return `
                    <div class="stock-card">
                        <div class="stock-header">
                            <div>
                                <div class="stock-name">${stock.name}</div>
                                <div class="stock-code">${stock.code}</div>
                                <span class="sector-tag">${stock.sector}</span>
                            </div>
                            <div class="score-badge ${scoreClass}">${stock.score}</div>
                        </div>
                        
                        <div class="price-section">
                            <span class="price">¥${stock.price.toFixed(2)}</span>
                            <span class="change ${changeClass}">${changeSign}${stock.change.toFixed(2)} (${changeSign}${stock.change_pct.toFixed(2)}%)</span>
                        </div>
                        
                        <div class="metrics">
                            <div class="metric">
                                <div class="metric-label">市盈率 (PE)</div>
                                <div class="metric-value">${stock.pe || '-'}</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">市净率 (PB)</div>
                                <div class="metric-value">${stock.pb || '-'}</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">ROE</div>
                                <div class="metric-value">${stock.roe ? stock.roe + '%' : '-'}</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">净利润率</div>
                                <div class="metric-value">${stock.net_margin ? stock.net_margin + '%' : '-'}</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">营收增长</div>
                                <div class="metric-value" style="color: ${stock.revenue_growth >= 0 ? '#4ade80' : '#ef4444'}">${stock.revenue_growth || '-'}%</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">利润增长</div>
                                <div class="metric-value" style="color: ${stock.profit_growth >= 0 ? '#4ade80' : '#ef4444'}">${stock.profit_growth || '-'}%</div>
                            </div>
                        </div>
                    </div>
                    `;
                }).join('');
                
            } catch (e) {
                grid.innerHTML = '<div class="loading">⚠️ 加载失败: ' + e.message + '</div>';
            }
        }
        
        // 搜索股票
        async function searchStock() {
            const input = document.getElementById('searchInput');
            const query = input.value.trim();
            
            if (!query) {
                alert('请输入股票代码');
                return;
            }
            
            const resultDiv = document.getElementById('searchResult');
            const watchlistDiv = document.getElementById('watchlistSection');
            resultDiv.innerHTML = '<div class="loading">正在查询...</div>';
            watchlistDiv.style.display = 'none';
            
            try {
                const response = await fetch('/api/search?q=' + encodeURIComponent(query));
                const data = await response.json();
                
                if (data.error) {
                    resultDiv.innerHTML = '<div class="loading">⚠️ ' + data.error + '</div>';
                    return;
                }
                
                if (data.stocks && data.stocks.length > 0) {
                    const stocks = data.stocks;
                    resultDiv.innerHTML = stocks.map(stock => renderStockCard(stock)).join('');
                } else {
                    resultDiv.innerHTML = '<div class="loading">未找到相关股票，请检查代码是否正确</div>';
                }
                
            } catch (e) {
                resultDiv.innerHTML = '<div class="loading">⚠️ 查询失败: ' + e.message + '</div>';
            }
        }
        
        // 回车搜索
        function handleSearch(event) {
            if (event.key === 'Enter') {
                searchStock();
            }
        }
        
        // 显示关注列表
        async function showWatchlist() {
            const resultDiv = document.getElementById('searchResult');
            const watchlistDiv = document.getElementById('watchlistSection');
            const grid = document.getElementById('watchlistGrid');
            
            resultDiv.innerHTML = '';
            watchlistDiv.style.display = 'block';
            grid.innerHTML = '<div class="loading">正在获取数据...</div>';
            
            try {
                const response = await fetch('/api/stocks');
                const data = await response.json();
                
                if (data.error) {
                    grid.innerHTML = '<div class="loading">⚠️ ' + data.error + '</div>';
                    return;
                }
                
                const stocks = data.stocks || [];
                
                // 更新统计
                document.getElementById('totalStocks').textContent = stocks.length;
                const avgScore = stocks.length ? Math.round(stocks.reduce((a,b) => a + b.score, 0) / stocks.length) : 0;
                document.getElementById('avgScore').textContent = avgScore;
                
                // 排序
                stocks.sort((a, b) => b.score - a.score);
                
                grid.innerHTML = stocks.map(stock => renderStockCard(stock)).join('');
                
            } catch (e) {
                grid.innerHTML = '<div class="loading">⚠️ 加载失败: ' + e.message + '</div>';
            }
        }
        
        // 渲染股票卡片
        function renderStockCard(stock) {
            const scoreClass = stock.score >= 70 ? '' : (stock.score >= 50 ? 'score-mid' : 'score-low');
            const changeClass = stock.change >= 0 ? 'change-up' : 'change-down';
            const changeSign = stock.change >= 0 ? '+' : '';
            
            return `
            <div class="stock-card">
                <div class="stock-header">
                    <div>
                        <div class="stock-name">${stock.name}</div>
                        <div class="stock-code">${stock.code}</div>
                        <span class="sector-tag">${stock.sector || '未知'}</span>
                    </div>
                    <div class="score-badge ${scoreClass}">${stock.score}</div>
                </div>
                
                <div class="price-section">
                    <span class="price">¥${stock.price.toFixed(2)}</span>
                    <span class="change ${changeClass}">${changeSign}${stock.change.toFixed(2)} (${changeSign}${stock.change_pct.toFixed(2)}%)</span>
                </div>
                
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-label">市盈率 (PE)</div>
                        <div class="metric-value">${stock.pe || '-'}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">市净率 (PB)</div>
                        <div class="metric-value">${stock.pb || '-'}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">ROE</div>
                        <div class="metric-value">${stock.roe ? stock.roe + '%' : '-'}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">净利润率</div>
                        <div class="metric-value">${stock.net_margin ? stock.net_margin + '%' : '-'}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">营收增长</div>
                        <div class="metric-value" style="color: ${stock.revenue_growth >= 0 ? '#4ade80' : '#ef4444'}">${stock.revenue_growth || '-'}%</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">利润增长</div>
                        <div class="metric-value" style="color: ${stock.profit_growth >= 0 ? '#4ade80' : '#ef4444'}">${stock.profit_growth || '-'}%</div>
                    </div>
                </div>
            </div>
            `;
        }
        
        // 页面加载时获取数据
        showWatchlist();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/stocks')
def api_stocks():
    """API接口：获取所有股票数据"""
    stocks = []
    errors = []
    
    for code in WATCHLIST.keys():
        data = get_stock_data(code)
        if data.get("status") == "ok":
            stocks.append(data)
        else:
            errors.append(f"{code}: {data.get('message', 'unknown')}")
    
    if not stocks:
        return jsonify({"error": "无法获取数据，可能API限流，请在本地运行脚本", "stocks": []})
    
    return jsonify({
        "stocks": stocks,
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "errors": errors
    })

def search_stock_code(keyword: str) -> list:
    """根据关键词搜索股票代码"""
    try:
        # 尝试直接作为代码处理
        if keyword.isdigit() and len(keyword) == 6:
            # 验证代码是否有效
            secid = f"1.{keyword}" if keyword.startswith("6") else f"0.{keyword}"
            url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f57"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                if data.get("data") and data["data"].get("f57"):
                    return [{"code": keyword, "name": data["data"]["f57"]}]
        
        # 搜索股票名称
        url = f"https://searchapi.eastmoney.com/api/suggest/get?input={keyword}&type=14&count=10"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        results = []
        if data.get("QuotationCode"):
            for item in data["QuotationCode"][:10]:
                results.append({
                    "code": item.get("Code", ""),
                    "name": item.get("Name", "")
                })
        return results
        
    except Exception as e:
        return []

@app.route('/api/search')
def api_search():
    """API接口：搜索股票"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({"error": "请输入搜索关键词", "stocks": []})
    
    # 搜索股票代码
    search_results = search_stock_code(query)
    
    if not search_results:
        return jsonify({"error": "未找到相关股票", "stocks": []})
    
    # 获取搜索结果中每个股票的详细数据
    stocks = []
    for item in search_results:
        code = item["code"]
        name = item["name"]
        
        # 确定市场
        if code.startswith("6"):
            secid = f"1.{code}"
            market = "沪市"
        elif code.startswith("0") or code.startswith("3"):
            secid = f"0.{code}"
            market = "深市"
        else:
            secid = f"0.{code}"
            market = "深市"
        
        try:
            url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f44,f45,f57,f58,f84,f85,f116,f117,f127,f128,f162,f163,f164,f167,f168,f169,f170,f173,f177,f178,f187,f188,f189,f190,f191,f192"
            
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            if data.get("data"):
                d = data["data"]
                
                # 价格
                price = d.get("f43", 0) / 1000 if d.get("f43") else 0
                change = d.get("f44", 0) / 100 if d.get("f44") else 0
                change_pct = d.get("f45", 0) / 100 if d.get("f45") else 0
                
                # 估值
                pe = d.get("f162", 0)
                pb = d.get("f167", 0)
                
                # 盈利
                roe = d.get("f173", 0) if d.get("f173") else 0
                net_margin = d.get("f170", 0) if d.get("f170") else 0
                
                # 成长
                revenue_growth = d.get("f184", 0) if d.get("f184") else 0
                profit_growth = d.get("f190", 0) if d.get("f190") else 0
                
                # 计算评分
                score = calculate_score(roe, net_margin, pe, pb, profit_growth)
                
                stocks.append({
                    "code": code,
                    "name": name,
                    "sector": market,
                    "price": price,
                    "change": change,
                    "change_pct": change_pct,
                    "pe": pe,
                    "pb": pb,
                    "roe": roe,
                    "net_margin": net_margin,
                    "revenue_growth": revenue_growth,
                    "profit_growth": profit_growth,
                    "score": score,
                    "status": "ok"
                })
        except Exception as e:
            stocks.append({
                "code": code,
                "name": name,
                "sector": market,
                "status": "error",
                "message": str(e)
            })
    
    return jsonify({
        "stocks": stocks,
        "query": query,
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

if __name__ == '__main__':
    print("="*60)
    print("  巴菲特风格选股器 - Web可视化版")
    print("  访问地址: http://localhost:5000")
    print("="*60)
    app.run(host='0.0.0.0', port=5000, debug=True)
