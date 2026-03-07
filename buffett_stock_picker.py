#!/usr/bin/env python3
"""
巴菲特/芒格风格价值投资选股程序
Buffett-Munger Style Stock Screener for A-shares and H-shares
"""

from dataclasses import dataclass
from typing import List
from datetime import datetime

@dataclass
class Stock:
    code: str
    name: str
    market: str  # A股 or H股
    sector: str
    price: float
    pe: float
    pb: float
    roe: float
    gross_margin: float
    net_margin: float
    debt_ratio: float
    revenue_growth: float
    profit_growth: float
    free_cash_flow: float
    moat_score: int
    dividend_yield: float
    
    def score(self) -> float:
        score = 0
        # ROE (25分)
        if self.roe >= 20: score += 25
        elif self.roe >= 15: score += 20
        elif self.roe >= 12: score += 15
        elif self.roe >= 10: score += 10
        else: score += 5
        # 利润率 (15分)
        if self.gross_margin >= 40: score += 10
        elif self.gross_margin >= 30: score += 7
        elif self.gross_margin >= 20: score += 4
        if self.net_margin >= 15: score += 5
        elif self.net_margin >= 10: score += 3
        elif self.net_margin >= 5: score += 1
        # 负债 (15分)
        if self.debt_ratio < 30: score += 15
        elif self.debt_ratio < 40: score += 12
        elif self.debt_ratio < 50: score += 8
        elif self.debt_ratio < 60: score += 4
        # 现金流 (15分)
        if self.free_cash_flow > 100: score += 15
        elif self.free_cash_flow > 50: score += 12
        elif self.free_cash_flow > 20: score += 8
        elif self.free_cash_flow > 0: score += 4
        # 估值 (15分)
        if 0 < self.pe <= 15: score += 8
        elif self.pe <= 20: score += 6
        elif self.pe <= 25: score += 4
        elif self.pe <= 30: score += 2
        if 0 < self.pb <= 2: score += 7
        elif self.pb <= 3: score += 5
        elif self.pb <= 5: score += 3
        # 增长 (10分)
        if self.profit_growth >= 20: score += 6
        elif self.profit_growth >= 10: score += 4
        elif self.profit_growth >= 0: score += 2
        if self.revenue_growth >= 15: score += 4
        elif self.revenue_growth >= 10: score += 2
        elif self.revenue_growth >= 0: score += 1
        # 护城河 (5分)
        score += self.moat_score * 0.5
        return score
    
    def get_strengths(self) -> List[str]:
        s = []
        if self.roe >= 15: s.append(f"ROE {self.roe}%")
        if self.gross_margin >= 40: s.append(f"毛利率 {self.gross_margin}%")
        if self.net_margin >= 15: s.append(f"净利率 {self.net_margin}%")
        if self.debt_ratio < 40: s.append(f"负债率 {self.debt_ratio}%")
        if self.free_cash_flow > 50: s.append(f"现金流 {self.free_cash_flow}亿")
        if self.moat_score >= 8: s.append(f"护城河 {self.moat_score}/10")
        if self.pe < 20 and self.pe > 0: s.append(f"PE {self.pe}")
        if self.dividend_yield > 3: s.append(f"股息率 {self.dividend_yield}%")
        if self.profit_growth > 15: s.append(f"利润增长 {self.profit_growth}%")
        return s


def get_stocks() -> List[Stock]:
    return [
        # A股
        Stock("600519", "贵州茅台", "A股", "白酒", 1850, 28.5, 6.2, 32, 52, 25, 18, 15, 18, 350, 9, 3.5),
        Stock("000333", "美的集团", "A股", "家电", 65, 12.5, 3.2, 22, 25, 10, 62, 8, 10, 200, 8, 4.0),
        Stock("600036", "招商银行", "A股", "银行", 42, 6.5, 1.2, 15, 38, 28, 75, 6, 5, 1200, 7, 4.2),
        Stock("601318", "中国平安", "A股", "保险", 48, 9.8, 1.1, 12, 25, 12, 68, 8, 3, 500, 7, 5.5),
        Stock("002415", "海康威视", "A股", "安防", 32, 18.5, 5.8, 18, 45, 22, 38, 15, 12, 80, 8, 3.0),
        Stock("000858", "五粮液", "A股", "白酒", 140, 18.2, 5.5, 18, 38, 28, 32, 12, 15, 120, 8, 3.2),
        Stock("300750", "宁德时代", "A股", "新能源", 180, 25, 6.8, 15, 28, 15, 55, 25, 20, 150, 7, 1.5),
        Stock("600276", "恒瑞医药", "A股", "医药", 52, 45, 8.5, 12, 18, 12, 35, 2, 1, 60, 8, 2.0),
        Stock("002594", "比亚迪", "A股", "新能源车", 280, 32, 5.2, 15, 18, 5, 72, 25, 18, 180, 7, 1.0),
        Stock("600309", "万华化学", "A股", "化工", 95, 15, 4.5, 18, 22, 12, 58, 10, 8, 100, 6, 3.5),
        Stock("600887", "伊利股份", "A股", "食品", 28, 18, 5.8, 15, 32, 8, 52, 6, 5, 80, 7, 4.0),
        Stock("600900", "长江电力", "A股", "电力", 25, 18, 3.8, 10, 45, 28, 42, 5, 3, 200, 8, 4.5),
        Stock("603259", "药明康德", "A股", "医药", 75, 28, 8.2, 15, 35, 18, 38, 18, 15, 50, 7, 2.0),
        Stock("601888", "中国中免", "A股", "零售", 220, 35, 8.5, 15, 32, 15, 45, 20, 18, 100, 8, 2.5),
        # H股
        Stock("0700", "腾讯控股", "H股", "互联网", 380, 18.2, 8.5, 25, 45, 22, 38, 12, 18, 800, 9, 2.8),
        Stock("0941", "中国移动", "H股", "通信", 65, 10.5, 1.8, 10, 55, 32, 28, 8, 5, 1200, 8, 7.5),
        Stock("0939", "建设银行", "H股", "银行", 5.2, 4.5, 0.9, 12, 35, 25, 92, 4, 3, 2500, 6, 6.0),
        Stock("0912", "复星医药", "H股", "医药", 28, 12.5, 3.2, 15, 48, 18, 45, 12, 8, 60, 7, 3.5),
        Stock("1211", "比亚迪股份", "H股", "新能源车", 260, 28, 4.8, 18, 20, 6, 68, 22, 15, 150, 7, 1.2),
        Stock("1109", "华润置地", "H股", "房地产", 32, 8.5, 1.2, 8, 25, 18, 65, 5, 2, 80, 6, 4.8),
        Stock("0688", "中国海外", "H股", "房地产", 25, 6.8, 1.0, 10, 22, 15, 60, 8, 5, 120, 6, 5.0),
        Stock("0883", "中国海油", "H股", "能源", 12, 8, 2.8, 15, 38, 22, 35, 15, 12, 300, 8, 5.5),
        Stock("0386", "中国石化", "H股", "能源", 4.8, 7.5, 1.5, 10, 25, 8, 55, 5, 3, 400, 7, 6.5),
        Stock("1177", "中国生物制药", "H股", "医药", 4.2, 15, 4.5, 12, 42, 18, 40, 10, 8, 50, 7, 3.0),
    ]


def screen(stocks: List[Stock], market: str = "ALL") -> List[Stock]:
    filtered = []
    for s in stocks:
        if market != "ALL" and s.market != market:
            continue
        if s.roe < 10: continue
        if s.sector != "银行" and s.debt_ratio >= 70: continue
        if s.net_margin <= 0: continue
        if s.free_cash_flow <= 0: continue
        filtered.append(s)
    return sorted(filtered, key=lambda x: x.score(), reverse=True)


def main():
    print("="*70)
    print("  巴菲特/芒格风格价值投资选股报告")
    print("  Buffett-Munger Style Value Investing")
    print("="*70)
    print(f"  日期: {datetime.now().strftime('%Y-%m-%d')}")
    print("="*70)
    
    stocks = get_stocks()
    result = screen(stocks)
    
    print(f"\n筛选出 {len(result)} 只符合巴菲特标准的股票\n")
    
    # Top 10
    print("-"*70)
    print("【A股 + H股 Top 10 选股池】")
    print("-"*70)
    
    for i, s in enumerate(result[:10], 1):
        score = s.score()
        if score >= 80: rating = "★★★★★"
        elif score >= 70: rating = "★★★★☆"
        elif score >= 60: rating = "★★★☆☆"
        else: rating = "★★☆☆☆"
        
        print(f"\n{i:2}. {s.name:8} ({s.code:6}) {s.market} {s.sector:4}")
        print(f"    评分: {score:5.1f}/100 {rating}")
        print(f"    价格: ¥{s.price:8.2f}  PE: {s.pe:5.1f}  PB: {s.pb:4.1f}")
        print(f"    ROE: {s.roe:4.0f}%  毛利率: {s.gross_margin:4.0f}%  净利率: {s.net_margin:4.0f}%")
        print(f"    负债: {s.debt_ratio:4.0f}%  现金流: {s.free_cash_flow:6.0f}亿")
        print(f"    增长: 营收 {s.revenue_growth:+5.1f}%  利润 {s.profit_growth:+5.1f}%")
        print(f"    优势: {', '.join(s.get_strengths()[:5])}")
    
    print("\n" + "="*70)
    print("【投资建议】")
    print("="*70)
    print("""
基于巴菲特/芒格价值投资理念:

✓ 首选评分75+：盈利强、财务健康、估值合理
○ 谨慎评分60-75：需进一步分析
✗ 回避评分60-：不符合价值投资标准

风险提示:
• 数据为模拟数据，投资前请核实
• 过往业绩不代表未来表现
• 建议分散投资，不要集中单只股票
""")
    
    # 保存结果
    with open("/workspace/stock_pick_result.txt", "w", encoding="utf-8") as f:
        f.write("巴菲特/芒格风格选股结果\n")
        f.write("="*50 + "\n")
        for i, s in enumerate(result[:10], 1):
            f.write(f"{i}. {s.name} ({s.code}) {s.market} 评分: {s.score():.1f}\n")
    
    print("\n结果已保存到: /workspace/stock_pick_result.txt")
    return result[:10]


if __name__ == "__main__":
    main()
