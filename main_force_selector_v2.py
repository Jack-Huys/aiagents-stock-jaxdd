#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主力选股优化版V2 - 高级筛选策略
在原有主力资金选股基础上，增加技术面、资金面、基本面、趋势等多维度筛选条件
显著提高选股成功率
"""

import pandas as pd
import pywencai
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import time
import akshare as ak
import numpy as np


class MainForceStockSelectorV2:
    """主力选股优化版V2 - 多维度智能筛选"""

    def __init__(self):
        self.raw_data = None
        self.filtered_stocks = None
        self.advanced_filtered = None

    def get_main_force_stocks(self, start_date: str = None, days_ago: int = None,
                              min_market_cap: float = None, max_market_cap: float = None) -> Tuple[bool, pd.DataFrame, str]:
        """
        获取主力资金净流入前100名股票

        Args:
            start_date: 开始日期，格式如"2025年10月1日"
            days_ago: 距今多少天
            min_market_cap: 最小市值限制
            max_market_cap: 最大市值限制

        Returns:
            (success, dataframe, message)
        """
        try:
            if not start_date:
                date_obj = datetime.now() - timedelta(days=days_ago)
                start_date = f"{date_obj.year}年{date_obj.month}月{date_obj.day}日"

            print(f"\n{'='*60}")
            print(f"🔍 主力选股V2 - 数据获取中")
            print(f"{'='*60}")
            print(f"开始日期: {start_date}")

            queries = [
                # 方案1: 完整查询
                f"{start_date}以来主力资金净流入排名，并计算区间涨跌幅，市值{min_market_cap}-{max_market_cap}亿之间，非科创非st，"
                f"所属同花顺行业，总市值，净利润，营收，市盈率，市净率，"
                f"盈利能力评分，成长能力评分，营运能力评分，偿债能力评分，"
                f"现金流评分，资产质量评分，流动性评分，资本充足性评分",

                # 方案2: 简化查询
                f"{start_date}以来主力资金净流入，并计算区间涨跌幅，市值{min_market_cap}-{max_market_cap}亿，非科创非st，"
                f"所属同花顺行业，总市值，净利润，营收，市盈率，市净率",

                # 方案3: 基础查询
                f"{start_date}以来主力资金净流入排名，并计算区间涨跌幅，市值{min_market_cap}-{max_market_cap}亿，非科创非st，"
                f"所属行业，总市值",

                # 方案4: 最简查询
                f"{start_date}以来主力资金净流入前100名，并计算区间涨跌幅，市值{min_market_cap}-{max_market_cap}亿，非st非科创板，所属行业，总市值",
            ]

            for i, query in enumerate(queries, 1):
                print(f"\n尝试方案 {i}/{len(queries)}...")

                try:
                    result = pywencai.get(query=query, loop=True)

                    if result is None:
                        print(f"  ⚠️ 方案{i}返回None")
                        continue

                    df_result = self._convert_to_dataframe(result)

                    if df_result is None or df_result.empty:
                        print(f"  ⚠️ 方案{i}数据为空")
                        continue

                    print(f"  ✅ 方案{i}成功！获取到 {len(df_result)} 只股票")
                    self.raw_data = df_result

                    return True, df_result, f"成功获取{len(df_result)}只股票数据"

                except Exception as e:
                    print(f"  ❌ 方案{i}失败: {str(e)}")
                    time.sleep(2)
                    continue

            return False, None, "所有查询方案都失败了"

        except Exception as e:
            return False, None, f"获取主力选股数据失败: {str(e)}"

    def _convert_to_dataframe(self, result) -> pd.DataFrame:
        """转换问财返回结果为DataFrame"""
        try:
            if isinstance(result, pd.DataFrame):
                return result
            elif isinstance(result, dict):
                if 'tableV1' in result:
                    table_data = result['tableV1']
                    if isinstance(table_data, pd.DataFrame):
                        return table_data
                    elif isinstance(table_data, list):
                        return pd.DataFrame(table_data)
                return pd.DataFrame([result])
            elif isinstance(result, list):
                return pd.DataFrame(result)
            return None
        except Exception as e:
            print(f"  转换DataFrame失败: {e}")
            return None

    def filter_stocks_basic(self, df: pd.DataFrame,
                            max_range_change: float = None,
                            min_market_cap: float = None,
                            max_market_cap: float = None) -> pd.DataFrame:
        """
        基础筛选 - 与原版相同
        """
        if df is None or df.empty:
            return df

        filtered_df = df.copy()

        # 1. 筛选区间涨跌幅
        interval_pct_col = self._find_column(df, [
            '区间涨跌幅:前复权', '区间涨跌幅(%)', '区间涨跌幅',
            '涨跌幅:前复权', '涨跌幅(%)', '涨跌幅'
        ])

        if interval_pct_col:
            filtered_df[interval_pct_col] = pd.to_numeric(filtered_df[interval_pct_col], errors='coerce')
            filtered_df = filtered_df[
                (filtered_df[interval_pct_col].notna()) &
                (filtered_df[interval_pct_col] < max_range_change)
            ]

        # 2. 筛选市值
        market_cap_col = self._find_column(df, ['总市值', '市值'])
        if market_cap_col:
            filtered_df[market_cap_col] = pd.to_numeric(filtered_df[market_cap_col], errors='coerce')
            max_val = filtered_df[market_cap_col].max()
            if max_val > 100000:
                filtered_df[market_cap_col] = filtered_df[market_cap_col] / 100000000

            filtered_df = filtered_df[
                (filtered_df[market_cap_col].notna()) &
                (filtered_df[market_cap_col] >= min_market_cap) &
                (filtered_df[market_cap_col] <= max_market_cap)
            ]

        # 3. 去除ST股票
        name_col = self._find_column(df, ['股票简称', '名称'])
        if name_col and name_col in filtered_df.columns:
            filtered_df = filtered_df[~filtered_df[name_col].str.contains('ST', na=False)]

        self.filtered_stocks = filtered_df
        return filtered_df

    def filter_stocks_advanced(self, df: pd.DataFrame,
                               tech_params: Dict = None,
                               fund_params: Dict = None,
                               fundamental_params: Dict = None,
                               trend_params: Dict = None) -> pd.DataFrame:
        """
        高级筛选 - V2新增多维度筛选

        Args:
            df: 基础筛选后的股票数据
            tech_params: 技术面筛选参数
            fund_params: 资金面筛选参数
            fundamental_params: 基本面筛选参数
            trend_params: 趋势筛选参数

        Returns:
            高级筛选后的DataFrame
        """
        if df is None or df.empty:
            return df

        # 默认参数
        tech_params = tech_params or {}
        fund_params = fund_params or {}
        fundamental_params = fundamental_params or {}
        trend_params = trend_params or {}

        print(f"\n{'='*60}")
        print(f"🔍 高级多维度筛选中...")
        print(f"{'='*60}")

        original_count = len(df)
        filtered_df = df.copy()

        # ========== 1. 技术面筛选 ==========
        print(f"\n📊 技术面筛选...")
        if tech_params:
            # RSI筛选
            rsi_min = tech_params.get('rsi_min', 30)
            rsi_max = tech_params.get('rsi_max', 80)
            print(f"  RSI区间: {rsi_min}-{rsi_max}")

            # MACD金叉筛选
            macd_golden_cross = tech_params.get('macd_golden_cross', False)
            if macd_golden_cross:
                print(f"  MACD金叉: 需要在5日内出现")

            # 均线多头排列
            ma_alignment = tech_params.get('ma_alignment', False)
            if ma_alignment:
                print(f"  均线多头排列: MA5>MA10>MA20>MA60")

            # 突破关键位置
            price_breakout = tech_params.get('price_breakout_20ma', False)
            if price_breakout:
                print(f"  突破20日均线: 需要")

            # 布林带支撑
            boll_support = tech_params.get('boll_mid_support', False)
            if boll_support:
                print(f"  布林带中轨支撑: 需要")

        # ========== 2. 资金面筛选 ==========
        print(f"\n💰 资金面筛选...")
        if fund_params:
            # 主力净流入占比
            main_fund_ratio_min = fund_params.get('main_fund_ratio_min', 10)
            print(f"  主力净流入占比 > {main_fund_ratio_min}%")

            # 连续净流入天数
            consecutive_days = fund_params.get('consecutive_days_min', 3)
            print(f"  连续净流入天数 >= {consecutive_days}天")

            # 超大单净流入
            super_large_inflow = fund_params.get('super_large_inflow', False)
            if super_large_inflow:
                print(f"  超大单净流入: 需要")

            # 北向资金增持
            north_bound = fund_params.get('north_bound_increase', False)
            if north_bound:
                print(f"  北向资金增持: 需要")

        # ========== 3. 基本面筛选 ==========
        print(f"\n📈 基本面筛选...")
        if fundamental_params:
            roe_min = fundamental_params.get('roe_min', 0)
            if roe_min > 0:
                print(f"  ROE > {roe_min}%")

            profit_growth_min = fundamental_params.get('profit_growth_min', 0)
            if profit_growth_min > 0:
                print(f"  净利润增长 > {profit_growth_min}%")

            debt_ratio_max = fundamental_params.get('debt_ratio_max', 100)
            print(f"  资产负债率 < {debt_ratio_max}%")

            peg_max = fundamental_params.get('peg_max', 5)
            if peg_max < 5:
                print(f"  PEG < {peg_max}")

            dividend_min = fundamental_params.get('dividend_min', 0)
            if dividend_min > 0:
                print(f"  股息率 > {dividend_min}%")

        # ========== 4. 趋势筛选 ==========
        print(f"\n📉 趋势筛选...")
        if trend_params:
            amplitude_min = trend_params.get('amplitude_min', 0)
            amplitude_max = trend_params.get('amplitude_max', 100)
            print(f"  振幅区间: {amplitude_min}%-{amplitude_max}%")

            above_year_ma = trend_params.get('above_year_ma', False)
            if above_year_ma:
                print(f"  股价在年线上方: 需要")

            chip_concentration = trend_params.get('chip_concentration', False)
            if chip_concentration:
                print(f"  筹码集中度提升: 需要")

        print(f"\n  基础筛选后: {original_count} 只")

        # 保存高级筛选结果
        self.advanced_filtered = filtered_df
        return filtered_df

    def get_technical_indicators(self, symbol: str, period: str = "3mo") -> Optional[Dict]:
        """
        获取单只股票的技术指标（用于高级筛选）

        Args:
            symbol: 股票代码
            period: 数据周期

        Returns:
            技术指标字典
        """
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        # 创建带重试的session
        session = requests.Session()
        retry = Retry(total=2, backoff_factor=0.5, status_forcelist=[502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        try:
            # 获取日线数据（带重试）
            max_retries = 3
            df = None

            for attempt in range(max_retries):
                try:
                    df = ak.stock_zh_a_hist(symbol=symbol, period="daily",
                                            start_date=(datetime.now() - timedelta(days=150)).strftime('%Y%m%d'),
                                            end_date=datetime.now().strftime('%Y%m%d'),
                                            adjust='qfq')
                    break
                except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as e:
                    if attempt < max_retries - 1:
                        print(f"  第{attempt+1}次获取{symbol}数据失败，1秒后重试...")
                        time.sleep(1)
                    else:
                        raise

            if df is None or df.empty or len(df) < 20:
                return None

            # 计算技术指标
            close = df['收盘'].astype(float)
            high = df['最高'].astype(float)
            low = df['最低'].astype(float)
            volume = df['成交量'].astype(float)

            # ========== MA均线 ==========
            ma5 = close.rolling(5).mean()
            ma10 = close.rolling(10).mean()
            ma20 = close.rolling(20).mean()
            ma60 = close.rolling(60).mean()

            # ========== RSI ==========
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(6).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(6).mean()
            rs = gain / loss
            rsi6 = 100 - (100 / (1 + rs))

            # ========== MACD ==========
            ema12 = close.ewm(span=12).mean()
            ema26 = close.ewm(span=26).mean()
            macd_dif = ema12 - ema26
            macd_dea = macd_dif.ewm(span=9).mean()
            macd_hist = (macd_dif - macd_dea) * 2

            # ========== KDJ ==========
            n = 9
            low_n = low.rolling(n).min()
            high_n = high.rolling(n).max()
            rsv = (close - low_n) / (high_n - low_n) * 100
            rsv = rsv.fillna(50)
            k = rsv.ewm(com=2).mean()
            d = k.ewm(com=2).mean()
            j = 3 * k - 2 * d

            # ========== 布林带 ==========
            boll_mid = close.rolling(20).mean()
            boll_std = close.rolling(20).std()
            boll_upper = boll_mid + 2 * boll_std
            boll_lower = boll_mid - 2 * boll_std

            # ========== 量价配合分析 ==========
            # 成交量与价格变动的关系
            volume_change = volume.pct_change()
            price_change = close.pct_change()

            # 量增价涨(1)/量增价跌(-1)/量缩价稳(0)
            vol_price_score = 0
            vol_price_signals = []

            # 最近5天量价配合分析
            for i in range(-5, 0):
                if i >= -len(volume_change) and i >= -len(price_change):
                    vol_ch = volume_change.iloc[i] if not pd.isna(volume_change.iloc[i]) else 0
                    price_ch = price_change.iloc[i] if not pd.isna(price_change.iloc[i]) else 0

                    if vol_ch > 0.1 and price_ch > 0.01:
                        vol_price_signals.append(1)  # 量增价涨
                    elif vol_ch > 0.1 and price_ch < -0.01:
                        vol_price_signals.append(-1)  # 量增价跌（背离）
                    elif vol_ch < -0.1 and abs(price_ch) < 0.01:
                        vol_price_signals.append(0.5)  # 量缩价稳
                    else:
                        vol_price_signals.append(0)

            vol_price_score = sum(vol_price_signals) / len(vol_price_signals) * 20 if vol_price_signals else 0

            # 量比
            avg_volume_5 = volume.tail(5).mean()
            avg_volume_10 = volume.tail(10).mean()
            volume_ratio = avg_volume_5 / avg_volume_10 if avg_volume_10 > 0 else 1

            # 能量潮OBV
            obv = (np.sign(close.diff()) * volume).cumsum()
            obv_trend = 1 if obv.iloc[-1] > obv.iloc[-5] else -1 if obv.iloc[-1] < obv.iloc[-5] else 0

            # 成交量加权价格变化
            price_volume_corr = close.diff().corr(volume) if len(close) > 5 else 0

            # ========== 当前值 ==========
            current_price = close.iloc[-1]
            current_ma5 = ma5.iloc[-1]
            current_ma10 = ma10.iloc[-1]
            current_ma20 = ma20.iloc[-1]
            current_ma60 = ma60.iloc[-1] if len(ma60) >= 60 else None
            current_rsi6 = rsi6.iloc[-1]
            current_macd_dif = macd_dif.iloc[-1]
            current_macd_dea = macd_dea.iloc[-1]
            current_macd_hist = macd_hist.iloc[-1]
            current_k = k.iloc[-1]
            current_d = d.iloc[-1]
            current_j = j.iloc[-1]
            current_boll_mid = boll_mid.iloc[-1]
            current_boll_upper = boll_upper.iloc[-1]
            current_boll_lower = boll_lower.iloc[-1]

            # ========== 判断条件 ==========
            # 1. RSI健康区间
            rsi_healthy = 30 <= current_rsi6 <= 80

            # 2. MACD金叉 (DIF上穿DEA)
            macd_golden_cross_days = 0
            for i in range(1, min(11, len(macd_hist))):
                if macd_hist.iloc[-i-1] < 0 and macd_hist.iloc[-i] >= 0:
                    macd_golden_cross_days = i
                    break

            # 3. MACD死叉
            macd_dead_cross_days = 0
            for i in range(1, min(11, len(macd_hist))):
                if macd_hist.iloc[-i-1] > 0 and macd_hist.iloc[-i] <= 0:
                    macd_dead_cross_days = i
                    break

            # 4. KDJ金叉
            kdj_golden_cross_days = 0
            for i in range(1, min(11, len(k))):
                if k.iloc[-i-1] < d.iloc[-i-1] and k.iloc[-i] >= d.iloc[-i]:
                    kdj_golden_cross_days = i
                    break

            # 5. KDJ超买超卖
            kdj_overbought = current_k > 80 and current_d > 80  # 超买
            kdj_oversold = current_k < 20 and current_d < 20    # 超卖

            # 6. 均线多头排列
            ma_alignment = False
            if current_ma5 and current_ma10 and current_ma20:
                if current_ma60:
                    ma_alignment = current_ma5 > current_ma10 > current_ma20 > current_ma60
                else:
                    ma_alignment = current_ma5 > current_ma10 > current_ma20

            # 7. 均线空头排列
            ma_bearish = False
            if current_ma5 and current_ma10 and current_ma20:
                if current_ma60:
                    ma_bearish = current_ma5 < current_ma10 < current_ma20 < current_ma60
                else:
                    ma_bearish = current_ma5 < current_ma10 < current_ma20

            # 8. 突破20日均线
            price_breakout_20ma = current_price > current_ma20

            # 9. 布林带中轨支撑
            boll_mid_support = current_price >= current_boll_mid

            # 10. 振幅
            recent_high = high.tail(20).max()
            recent_low = low.tail(20).min()
            amplitude = (recent_high - recent_low) / recent_low * 100 if recent_low > 0 else 0

            # 11. 股价位置（相对布林带）
            boll_position = (current_price - current_boll_lower) / (current_boll_upper - current_boll_lower) * 100 if current_boll_upper > current_boll_lower else 50

            return {
                'symbol': symbol,
                'current_price': current_price,
                # MA
                'ma5': current_ma5,
                'ma10': current_ma10,
                'ma20': current_ma20,
                'ma60': current_ma60,
                'ma_alignment': ma_alignment,
                'ma_bearish': ma_bearish,
                # RSI
                'rsi6': current_rsi6,
                'rsi_healthy': rsi_healthy,
                # MACD
                'macd_dif': current_macd_dif,
                'macd_dea': current_macd_dea,
                'macd_hist': current_macd_hist,
                'macd_golden_cross_days': macd_golden_cross_days,
                'macd_dead_cross_days': macd_dead_cross_days,
                # KDJ
                'kdj_k': current_k,
                'kdj_d': current_d,
                'kdj_j': current_j,
                'kdj_golden_cross_days': kdj_golden_cross_days,
                'kdj_overbought': kdj_overbought,
                'kdj_oversold': kdj_oversold,
                # 布林带
                'boll_mid': current_boll_mid,
                'boll_upper': current_boll_upper,
                'boll_lower': current_boll_lower,
                'boll_mid_support': boll_mid_support,
                'boll_position': boll_position,
                # 量价
                'amplitude': amplitude,
                'volume_ratio': volume_ratio,
                'vol_price_score': vol_price_score,
                'obv_trend': obv_trend,
                'price_volume_corr': price_volume_corr,
                # 状态
                'price_breakout_20ma': price_breakout_20ma,
                'data_valid': True
            }

        except Exception as e:
            print(f"  ⚠️ 获取{symbol}技术指标失败: {e}")
            return None

    def get_fund_flow_indicators(self, symbol: str, days: int = 5) -> Optional[Dict]:
        """
        获取资金流向指标

        Args:
            symbol: 股票代码
            days: 查询天数

        Returns:
            资金流向指标字典
        """
        try:
            # 获取资金流向数据
            df = ak.stock_individual_fund_flow(stock=symbol, market="sh" if symbol.startswith('6') else "sz")

            if df is None or df.empty:
                return None

            # 主力资金净流入占比
            main_net_inflow_cols = [c for c in df.columns if '主力净流入' in c]
            if not main_net_inflow_cols:
                return None

            main_col = main_net_inflow_cols[0]

            # 最近N天主力净流入
            recent_days = df.head(days)
            main_inflow = recent_days[main_col].sum()

            # 超大单净流入
            super_cols = [c for c in df.columns if '超大单' in c and '净流入' in c]
            super_inflow = 0
            if super_cols:
                super_inflow = recent_days[super_cols[0]].sum()

            # 计算主力净流入占比
            # 需要成交额数据
            amount_cols = [c for c in df.columns if '成交额' in c or '成交' in c]
            total_amount = 0
            if amount_cols:
                total_amount = recent_days[amount_cols[0]].sum()
                if total_amount > 0:
                    main_ratio = main_inflow / total_amount * 100
                else:
                    main_ratio = 0
            else:
                main_ratio = 0

            # 连续净流入天数
            consecutive_days = 0
            for i in range(len(df)):
                if df[main_col].iloc[i] > 0:
                    consecutive_days += 1
                else:
                    break

            return {
                'symbol': symbol,
                'main_inflow': main_inflow,
                'main_ratio': main_ratio,
                'super_inflow': super_inflow,
                'consecutive_days': consecutive_days,
                'data_valid': True
            }

        except Exception as e:
            print(f"  ⚠️ 获取{symbol}资金流向失败: {e}")
            return None

    def apply_technical_filters(self, df: pd.DataFrame, params: Dict, indicators_cache: Dict = None) -> pd.DataFrame:
        """
        对候选股票应用技术面筛选

        Args:
            df: 候选股票
            params: 筛选参数
            indicators_cache: 已有指标缓存

        Returns:
            筛选后的DataFrame
        """
        if df is None or df.empty:
            return df

        # 如果没有技术面筛选参数，返回原数据
        if not params or not any(params.values()):
            return df

        symbols = df['股票代码'].tolist()
        valid_symbols = []
        tech_info_list = []

        print(f"\n  开始获取{len(symbols)}只股票的技术指标...")

        for i, symbol in enumerate(symbols):
            # 进度显示
            if (i + 1) % 5 == 0 or i == len(symbols) - 1:
                print(f"  进度: {i+1}/{len(symbols)}")

            # 检查缓存
            if indicators_cache and symbol in indicators_cache:
                tech_info = indicators_cache[symbol]
            else:
                tech_info = self.get_technical_indicators(symbol)
                if indicators_cache is not None:
                    indicators_cache[symbol] = tech_info
                # 请求间隔，避免被断连
                time.sleep(0.3)

            if tech_info is None:
                continue

            # 应用筛选条件
            rsi_min = params.get('rsi_min', 30)
            rsi_max = params.get('rsi_max', 80)
            rsi = tech_info.get('rsi6', 50)

            # RSI筛选
            if not (rsi_min <= rsi <= rsi_max):
                continue

            # MACD金叉筛选
            if params.get('macd_golden_cross', False):
                golden_days = params.get('macd_golden_cross_days', 5)
                if tech_info.get('macd_golden_cross_days', 0) > golden_days:
                    continue

            # 均线多头排列
            if params.get('ma_alignment', False):
                if not tech_info.get('ma_alignment', False):
                    continue

            # 突破20日均线
            if params.get('price_breakout_20ma', False):
                if not tech_info.get('price_breakout_20ma', False):
                    continue

            # 布林带中轨支撑
            if params.get('boll_mid_support', False):
                if not tech_info.get('boll_mid_support', False):
                    continue

            # 振幅筛选
            amplitude_min = params.get('amplitude_min', 0)
            amplitude_max = params.get('amplitude_max', 100)
            amplitude = tech_info.get('amplitude', 50)
            if not (amplitude_min <= amplitude <= amplitude_max):
                continue

            valid_symbols.append(symbol)
            tech_info_list.append(tech_info)

        print(f"  技术面筛选后: {len(valid_symbols)}/{len(symbols)} 只")

        # 返回筛选后的DataFrame
        return df[df['股票代码'].isin(valid_symbols)]

    def get_top_stocks(self, df: pd.DataFrame, top_n: int = None) -> pd.DataFrame:
        """获取主力资金净流入前N名"""
        if df is None or df.empty:
            return df

        main_fund_col = self._find_column(df, [
            '区间主力资金流向', '区间主力资金净流入',
            '主力资金流向', '主力资金净流入', '主力净流入'
        ])

        if main_fund_col:
            df[main_fund_col] = pd.to_numeric(df[main_fund_col], errors='coerce')
            top_df = df.nlargest(top_n, main_fund_col)
            return top_df
        else:
            return df.head(top_n)

    def _find_column(self, df: pd.DataFrame, patterns: List[str]) -> Optional[str]:
        """智能匹配列名"""
        for pattern in patterns:
            matching = [col for col in df.columns if pattern in col]
            if matching:
                return matching[0]
        return None

    def format_stock_list_for_analysis(self, df: pd.DataFrame) -> List[Dict]:
        """格式化股票列表"""
        if df is None or df.empty:
            return []

        stock_list = []

        for idx, row in df.iterrows():
            stock_data = {
                'symbol': row.get('股票代码', 'N/A'),
                'name': row.get('股票简称', row.get('名称', 'N/A')),
                'industry': self._get_value(row, df.columns, ['所属同花顺行业', '所属行业']),
                'market_cap': self._get_value(row, df.columns, ['总市值']),
                'range_change': self._get_value(row, df.columns, [
                    '区间涨跌幅:前复权', '区间涨跌幅(%)', '区间涨跌幅', '涨跌幅'
                ]),
                'main_fund_inflow': self._get_value(row, df.columns, [
                    '区间主力资金流向', '区间主力资金净流入', '主力资金净流入', '主力净流入'
                ]),
                'pe_ratio': self._get_value(row, df.columns, ['市盈率']),
                'pb_ratio': self._get_value(row, df.columns, ['市净率']),
                'roe': self._get_value(row, df.columns, ['净资产收益率', 'ROE']),
                'profit_growth': self._get_value(row, df.columns, ['净利润同比增长', '利润增长率']),
                'scores': {},
                'raw_data': row.to_dict()
            }

            # 提取评分
            for col in df.columns:
                if '评分' in col:
                    stock_data['scores'][col] = row.get(col, 'N/A')

            stock_list.append(stock_data)

        return stock_list

    def _get_value(self, row: pd.Series, columns, patterns: List[str]) -> any:
        """智能获取值"""
        for pattern in patterns:
            for col in columns:
                if pattern in col:
                    return row.get(col, 'N/A')
        return 'N/A'


class AdvancedFilterConfig:
    """高级筛选配置类"""

    # 预设策略
    STRATEGIES = {
        '激进型': {
            'description': '追求短期爆发，侧重资金面和技术面',
            'tech': {
                'rsi_min': 40,
                'rsi_max': 80,
                'macd_golden_cross': True,
                'macd_golden_cross_days': 5,
                'ma_alignment': False,
                'price_breakout_20ma': True,
                'boll_mid_support': False,
                'amplitude_min': 10,
                'amplitude_max': 40,
            },
            'fund': {
                'main_fund_ratio_min': 20,
                'consecutive_days_min': 3,
                'super_large_inflow': True,
                'north_bound_increase': False,
            },
            'fundamental': {
                'roe_min': 5,
                'profit_growth_min': 0,
                'debt_ratio_max': 80,
                'peg_max': 3,
                'dividend_min': 0,
            },
            'trend': {
                'above_year_ma': False,
                'chip_concentration': False,
            }
        },
        '稳健型': {
            'description': '追求稳定收益，平衡各维度',
            'tech': {
                'rsi_min': 35,
                'rsi_max': 75,
                'macd_golden_cross': True,
                'macd_golden_cross_days': 10,
                'ma_alignment': True,
                'price_breakout_20ma': True,
                'boll_mid_support': True,
                'amplitude_min': 8,
                'amplitude_max': 35,
            },
            'fund': {
                'main_fund_ratio_min': 15,
                'consecutive_days_min': 5,
                'super_large_inflow': False,
                'north_bound_increase': True,
            },
            'fundamental': {
                'roe_min': 8,
                'profit_growth_min': 5,
                'debt_ratio_max': 65,
                'peg_max': 2,
                'dividend_min': 1,
            },
            'trend': {
                'above_year_ma': True,
                'chip_concentration': True,
            }
        },
        '价值型': {
            'description': '追求长期价值，侧重基本面',
            'tech': {
                'rsi_min': 30,
                'rsi_max': 70,
                'macd_golden_cross': False,
                'ma_alignment': False,
                'price_breakout_20ma': False,
                'boll_mid_support': True,
                'amplitude_min': 5,
                'amplitude_max': 30,
            },
            'fund': {
                'main_fund_ratio_min': 10,
                'consecutive_days_min': 3,
                'super_large_inflow': False,
                'north_bound_increase': False,
            },
            'fundamental': {
                'roe_min': 12,
                'profit_growth_min': 10,
                'debt_ratio_max': 60,
                'peg_max': 1.5,
                'dividend_min': 2,
            },
            'trend': {
                'above_year_ma': True,
                'chip_concentration': True,
            }
        },
        '自定义': {
            'description': '自定义筛选参数',
            'tech': {},
            'fund': {},
            'fundamental': {},
            'trend': {}
        }
    }

    @classmethod
    def get_strategy(cls, name: str) -> Dict:
        """获取策略配置"""
        return cls.STRATEGIES.get(name, cls.STRATEGIES['稳健型'])

    @classmethod
    def get_all_strategies(cls) -> List[str]:
        """获取所有策略名称"""
        return list(cls.STRATEGIES.keys())


# 全局实例
main_force_selector_v2 = MainForceStockSelectorV2()
advanced_filter_config = AdvancedFilterConfig()


class MultiDimensionScorer:
    """多维度评分加权排序类"""

    # 各策略的权重配置（已增加行业相对强弱和风控维度）
    STRATEGY_WEIGHTS = {
        '激进型': {
            'description': '追求短期爆发，侧重资金面和技术面',
            'tech': 0.25,      # 技术面权重25%
            'fund': 0.30,      # 资金面权重30%
            'fundamental': 0.10,  # 基本面权重10%
            'trend': 0.10,     # 趋势面权重10%
            'industry': 0.10,  # 行业相对强弱10%
            'wencai': 0.10,    # 问财评分权重10%
            'risk': 0.05,      # 风控评分5%
        },
        '稳健型': {
            'description': '追求稳定收益，平衡各维度',
            'tech': 0.15,
            'fund': 0.20,
            'fundamental': 0.20,
            'trend': 0.15,
            'industry': 0.10,
            'wencai': 0.10,
            'risk': 0.10,
        },
        '价值型': {
            'description': '追求长期价值，侧重基本面',
            'tech': 0.05,
            'fund': 0.10,
            'fundamental': 0.35,
            'trend': 0.10,
            'industry': 0.15,
            'wencai': 0.15,
            'risk': 0.10,
        },
        '自定义': {
            'description': '自定义权重',
            'tech': 0.20,
            'fund': 0.20,
            'fundamental': 0.20,
            'trend': 0.10,
            'industry': 0.10,
            'wencai': 0.10,
            'risk': 0.10,
        }
    }

    # 各维度内部指标权重
    TECH_WEIGHTS = {
        'rsi': 0.15,           # RSI健康度
        'macd': 0.15,          # MACD趋势
        'kdj': 0.15,           # KDJ指标
        'ma_alignment': 0.20,  # 均线多头
        'boll_position': 0.15, # 布林带位置
        'vol_price': 0.10,     # 量价配合
        'volume_ratio': 0.10,  # 量比
    }

    FUND_WEIGHTS = {
        'main_ratio': 0.35,    # 主力占比
        'consecutive_days': 0.30,  # 连续天数
        'super_inflow': 0.20,  # 超大单
        'north_bound': 0.15,   # 北向资金
    }

    FUNDAMENTAL_WEIGHTS = {
        'roe': 0.30,           # ROE
        'profit_growth': 0.25, # 利润增长
        'peg': 0.20,           # PEG
        'dividend': 0.15,      # 股息率
        'debt_ratio': 0.10,    # 资产负债率
    }

    TREND_WEIGHTS = {
        'amplitude': 0.30,     # 振幅
        'year_ma': 0.40,       # 年线位置
        'chip': 0.30,          # 筹码集中
    }

    @classmethod
    def get_weights(cls, strategy: str = '稳健型') -> Dict:
        """获取策略权重配置"""
        return cls.STRATEGY_WEIGHTS.get(strategy, cls.STRATEGY_WEIGHTS['稳健型'])

    @classmethod
    def calculate_technical_score(cls, tech_info: Dict) -> float:
        """计算技术面得分 (0-100)"""
        if not tech_info or not tech_info.get('data_valid'):
            return 50  # 默认中等分数

        score = 0

        # RSI健康度 (0-100)
        rsi = tech_info.get('rsi6', 50)
        if 30 <= rsi <= 70:
            rsi_score = 100 - abs(rsi - 50) * 1.5
        else:
            rsi_score = max(0, 50 - (abs(rsi - 70) if rsi > 70 else abs(rsi - 30)) * 2)
        score += rsi_score * cls.TECH_WEIGHTS['rsi']

        # MACD趋势 (0-100)
        macd_hist = tech_info.get('macd_hist', 0)
        macd_golden_days = tech_info.get('macd_golden_cross_days', 0)
        if macd_golden_days == 0:
            macd_score = 50 if macd_hist < 0 else 70
        else:
            macd_score = min(100, 60 + (7 - macd_golden_days) * 7)
        score += macd_score * cls.TECH_WEIGHTS['macd']

        # KDJ指标 (0-100)
        kdj_k = tech_info.get('kdj_k', 50)
        kdj_d = tech_info.get('kdj_d', 50)
        kdj_golden_days = tech_info.get('kdj_golden_cross_days', 0)
        kdj_overbought = tech_info.get('kdj_overbought', False)
        kdj_oversold = tech_info.get('kdj_oversold', False)

        if kdj_oversold:
            # 超卖区域，金叉即将形成，给较高分数
            kdj_score = 75
        elif kdj_overbought:
            # 超买区域，给较低分数
            kdj_score = 40
        elif kdj_golden_days > 0 and kdj_golden_days <= 5:
            # 刚金叉
            kdj_score = min(100, 70 + (6 - kdj_golden_days) * 6)
        else:
            # 正常区域
            kdj_score = 50 + (kdj_k - 50) * 0.3
        score += kdj_score * cls.TECH_WEIGHTS['kdj']

        # 均线多头排列 (0或100)
        ma_score = 100 if tech_info.get('ma_alignment') else 40
        score += ma_score * cls.TECH_WEIGHTS['ma_alignment']

        # 布林带位置 (0-100)
        boll_support = tech_info.get('boll_mid_support', False)
        price = tech_info.get('current_price', 0)
        boll_mid = tech_info.get('boll_mid', 0)
        boll_upper = tech_info.get('boll_upper', 0)
        boll_lower = tech_info.get('boll_lower', 0)

        if boll_upper > boll_lower:
            boll_position = (price - boll_lower) / (boll_upper - boll_lower) * 100
            if boll_support:
                boll_score = min(100, 60 + boll_position * 0.4)
            else:
                boll_score = max(0, boll_position - 40)
        else:
            boll_score = 50
        score += boll_score * cls.TECH_WEIGHTS['boll_position']

        # 量价配合 (0-100)
        vol_price_score = tech_info.get('vol_price_score', 0)
        vol_price_normalized = (vol_price_score + 20) / 40 * 100  # 归一化到0-100
        vol_price_normalized = min(100, max(0, vol_price_normalized))
        score += vol_price_normalized * cls.TECH_WEIGHTS['vol_price']

        # 量比 (0-100)
        volume_ratio = tech_info.get('volume_ratio', 1)
        if volume_ratio >= 1.5:
            vol_score = min(100, 60 + (volume_ratio - 1.5) * 20)
        elif volume_ratio >= 1:
            vol_score = 60 + (volume_ratio - 1) * 40
        else:
            vol_score = max(20, volume_ratio * 60)
        score += vol_score * cls.TECH_WEIGHTS['volume_ratio']

        return min(100, max(0, score))

    @classmethod
    def calculate_fund_score(cls, fund_info: Dict) -> float:
        """计算资金面得分 (0-100)"""
        if not fund_info or not fund_info.get('data_valid'):
            return 50

        score = 0

        # 主力净流入占比 (0-100)
        main_ratio = fund_info.get('main_ratio', 0)
        main_ratio_score = min(100, main_ratio * 3)  # 30%以上给满分
        score += main_ratio_score * cls.FUND_WEIGHTS['main_ratio']

        # 连续净流入天数 (0-100)
        consecutive_days = fund_info.get('consecutive_days', 0)
        consecutive_score = min(100, consecutive_days * 15)  # 7天以上给满分
        score += consecutive_score * cls.FUND_WEIGHTS['consecutive_days']

        # 超大单净流入 (0或100)
        super_inflow = fund_info.get('super_inflow', 0)
        super_score = 100 if super_inflow > 0 else 30
        score += super_score * cls.FUND_WEIGHTS['super_inflow']

        # 北向资金 (0或100)
        north = fund_info.get('north_bound', False)
        north_score = 100 if north else 50
        score += north_score * cls.FUND_WEIGHTS['north_bound']

        return min(100, max(0, score))

    @classmethod
    def calculate_fundamental_score(cls, stock_data: Dict, fundamental_params: Dict = None) -> float:
        """计算基本面得分 (0-100)"""
        if not stock_data:
            return 50

        params = fundamental_params or {}
        score = 0

        # ROE (0-100)
        roe = stock_data.get('roe', stock_data.get('净资产收益率', 0))
        try:
            roe = float(roe) if roe not in ['N/A', None, ''] else 0
        except:
            roe = 0
        roe_min = params.get('roe_min', 8)
        if roe >= roe_min:
            roe_score = min(100, 60 + (roe - roe_min) * 4)
        else:
            roe_score = max(0, (roe / roe_min) * 60) if roe_min > 0 else 0
        score += roe_score * cls.FUNDAMENTAL_WEIGHTS['roe']

        # 净利润增长 (0-100)
        profit_growth = stock_data.get('profit_growth', stock_data.get('净利润同比增长', 0))
        try:
            profit_growth = float(profit_growth) if profit_growth not in ['N/A', None, ''] else 0
        except:
            profit_growth = 0
        profit_growth_min = params.get('profit_growth_min', 0)
        if profit_growth >= profit_growth_min:
            growth_score = min(100, 50 + profit_growth * 2)
        else:
            growth_score = max(0, 30 + (profit_growth - profit_growth_min) * 2)
        score += growth_score * cls.FUNDAMENTAL_WEIGHTS['profit_growth']

        # PEG (0-100，越低越好)
        peg = stock_data.get('peg', 0)
        try:
            if isinstance(peg, str):
                peg = float(peg) if peg not in ['N/A', None, ''] else 2
            peg = float(peg) if peg else 2
        except:
            peg = 2
        peg_max = params.get('peg_max', 2)
        if peg <= peg_max:
            peg_score = min(100, (peg_max - peg + 0.5) * 40)
        else:
            peg_score = max(0, 50 - (peg - peg_max) * 10)
        score += peg_score * cls.FUNDAMENTAL_WEIGHTS['peg']

        # 股息率 (0-100)
        dividend = stock_data.get('dividend', stock_data.get('股息率', 0))
        try:
            dividend = float(dividend) if dividend not in ['N/A', None, ''] else 0
        except:
            dividend = 0
        dividend_min = params.get('dividend_min', 1)
        if dividend >= dividend_min:
            div_score = min(100, 60 + dividend * 8)
        else:
            div_score = max(0, (dividend / dividend_min) * 60) if dividend_min > 0 else 0
        score += div_score * cls.FUNDAMENTAL_WEIGHTS['dividend']

        # 资产负债率 (0-100，越低越好)
        debt_ratio = stock_data.get('debt_ratio', stock_data.get('资产负债率', 0))
        try:
            debt_ratio = float(debt_ratio) if debt_ratio not in ['N/A', None, ''] else 50
        except:
            debt_ratio = 50
        debt_max = params.get('debt_ratio_max', 65)
        if debt_ratio <= debt_max:
            debt_score = min(100, 60 + (debt_max - debt_ratio) * 2)
        else:
            debt_score = max(0, 50 - (debt_ratio - debt_max))
        score += debt_score * cls.FUNDAMENTAL_WEIGHTS['debt_ratio']

        return min(100, max(0, score))

    @classmethod
    def calculate_trend_score(cls, tech_info: Dict, trend_params: Dict = None) -> float:
        """计算趋势面得分 (0-100)"""
        if not tech_info:
            return 50

        params = trend_params or {}
        score = 0

        # 振幅得分 (0-100)
        amplitude = tech_info.get('amplitude', 10)
        amp_min = params.get('amplitude_min', 5)
        amp_max = params.get('amplitude_max', 35)
        if amp_min <= amplitude <= amp_max:
            amp_score = 100
        elif amplitude < amp_min:
            amp_score = max(0, amplitude / amp_min * 80)
        else:
            amp_score = max(0, 100 - (amplitude - amp_max) * 3)
        score += amp_score * cls.TREND_WEIGHTS['amplitude']

        # 年线位置 (0-100)
        year_ma = params.get('above_year_ma', False)
        price = tech_info.get('current_price', 0)
        ma60 = tech_info.get('ma60', 0)
        if year_ma and ma60 > 0:
            year_ma_score = 100 if price > ma60 else 40
        else:
            year_ma_score = 70  # 不要求时给中等分数
        score += year_ma_score * cls.TREND_WEIGHTS['year_ma']

        # 筹码集中 (0-100)
        chip = params.get('chip_concentration', False)
        chip_score = 100 if chip else 50  # 简化处理
        score += chip_score * cls.TREND_WEIGHTS['chip']

        return min(100, max(0, score))

    @classmethod
    def calculate_wencai_score(cls, stock_data: Dict) -> float:
        """计算问财评分得分 (0-100)"""
        if not stock_data:
            return 50

        scores = []
        score_cols = ['盈利能力评分', '成长能力评分', '营运能力评分', '偿债能力评分',
                      '现金流评分', '资产质量评分', '流动性评分', '资本充足性评分']

        for col in score_cols:
            value = stock_data.get(col, stock_data.get('scores', {}).get(col))
            if value not in ['N/A', None, '', 0]:
                try:
                    score = float(value)
                    if 0 <= score <= 100:
                        scores.append(score)
                except:
                    pass

        if scores:
            return sum(scores) / len(scores)
        return 50

    @classmethod
    def calculate_total_score(cls, stock_data: Dict, tech_info: Dict = None,
                            fund_info: Dict = None, strategy: str = '稳健型',
                            fundamental_params: Dict = None,
                            trend_params: Dict = None) -> Dict:
        """
        计算股票综合评分

        Returns:
            包含各维度得分和总分的字典
        """
        weights = cls.get_weights(strategy)

        # 各维度得分
        tech_score = cls.calculate_technical_score(tech_info) if tech_info else 50
        fund_score = cls.calculate_fund_score(fund_info) if fund_info else 50
        fundamental_score = cls.calculate_fundamental_score(stock_data, fundamental_params)
        trend_score = cls.calculate_trend_score(tech_info, trend_params)
        industry_score = IndustryRelativeStrength.calculate_industry_score(stock_data, tech_info)
        wencai_score = cls.calculate_wencai_score(stock_data)

        # 风控评分（风险越高分数越低）
        risk_report = RiskControlManager.generate_risk_report(stock_data, tech_info, fund_info)
        risk_score = risk_report.get('risk_assessment', {}).get('risk_score', 50)

        # 加权总分
        total_score = (
            tech_score * weights.get('tech', 0.20) +
            fund_score * weights.get('fund', 0.25) +
            fundamental_score * weights.get('fundamental', 0.25) +
            trend_score * weights.get('trend', 0.10) +
            industry_score * weights.get('industry', 0.10) +
            wencai_score * weights.get('wencai', 0.10) +
            risk_score * weights.get('risk', 0.10)
        )

        return {
            'total_score': round(total_score, 2),
            'tech_score': round(tech_score, 2),
            'fund_score': round(fund_score, 2),
            'fundamental_score': round(fundamental_score, 2),
            'trend_score': round(trend_score, 2),
            'industry_score': round(industry_score, 2),
            'wencai_score': round(wencai_score, 2),
            'risk_score': round(risk_score, 2),
            'weights': weights,
            'risk_report': risk_report
        }

    @classmethod
    def score_and_sort_stocks(cls, df: pd.DataFrame, tech_indicators_cache: Dict = None,
                             fund_indicators_cache: Dict = None,
                             strategy: str = '稳健型',
                             fundamental_params: Dict = None,
                             trend_params: Dict = None,
                             top_n: int = None) -> pd.DataFrame:
        """
        对候选股票进行多维度评分并排序

        Args:
            df: 候选股票DataFrame
            tech_indicators_cache: 技术指标缓存
            fund_indicators_cache: 资金指标缓存
            strategy: 策略类型
            fundamental_params: 基本面参数
            trend_params: 趋势参数
            top_n: 返回前N只

        Returns:
            排序后的DataFrame，包含评分信息
        """
        if df is None or df.empty:
            return df

        print(f"\n{'='*60}")
        print(f"📊 多维度评分加权排序中...")
        print(f"{'='*60}")
        print(f"策略类型: {strategy}")
        weights = cls.get_weights(strategy)
        print(f"权重配置: 技术面{weights.get('tech',0)*100:.0f}% | 资金面{weights.get('fund',0)*100:.0f}% | "
              f"基本面{weights.get('fundamental',0)*100:.0f}% | 趋势面{weights.get('trend',0)*100:.0f}% | "
              f"行业{weights.get('industry',0)*100:.0f}% | 风控{weights.get('risk',0)*100:.0f}%")

        scored_stocks = []

        for idx, row in df.iterrows():
            symbol = row.get('股票代码', '')

            # 获取技术指标
            tech_info = tech_indicators_cache.get(symbol) if tech_indicators_cache else None

            # 获取资金指标
            fund_info = fund_indicators_cache.get(symbol) if fund_indicators_cache else None

            # 计算评分
            stock_data = row.to_dict()
            scores = cls.calculate_total_score(
                stock_data=stock_data,
                tech_info=tech_info,
                fund_info=fund_info,
                strategy=strategy,
                fundamental_params=fundamental_params,
                trend_params=trend_params
            )

            # 添加到结果
            scored_row = stock_data.copy()
            scored_row['综合评分'] = scores['total_score']
            scored_row['技术面评分'] = scores['tech_score']
            scored_row['资金面评分'] = scores['fund_score']
            scored_row['基本面评分'] = scores['fundamental_score']
            scored_row['趋势面评分'] = scores['trend_score']
            scored_row['问财评分'] = scores['wencai_score']
            scored_row['评分明细'] = scores

            scored_stocks.append(scored_row)

        # 创建新的DataFrame
        result_df = pd.DataFrame(scored_stocks)

        # 按综合评分降序排序
        result_df = result_df.sort_values('综合评分', ascending=False)

        # 限制返回数量
        if top_n:
            result_df = result_df.head(top_n)

        # 重置索引
        result_df = result_df.reset_index(drop=True)

        print(f"\n  评分完成，共 {len(result_df)} 只股票")
        print(f"  评分前5名:")
        for i, (_, row) in enumerate(result_df.head(5).iterrows(), 1):
            print(f"    {i}. {row.get('股票代码', 'N/A')} {row.get('股票简称', 'N/A')} - "
                  f"综合评分:{row['综合评分']:.1f} "
                  f"(技:{row['技术面评分']:.1f} 资:{row['资金面评分']:.1f} "
                  f"基:{row['基本面评分']:.1f} 趋:{row['趋势面评分']:.1f})")

        return result_df


# 全局实例
multi_dimension_scorer = MultiDimensionScorer()


class IndustryRelativeStrength:
    """行业相对强弱分析类"""

    @classmethod
    def get_industry_index_data(cls, industry_code: str, days: int = 20) -> Optional[pd.DataFrame]:
        """
        获取行业指数数据

        Args:
            industry_code: 行业代码
            days: 统计天数

        Returns:
            行业指数DataFrame
        """
        try:
            # 使用通达信行业指数或板块指数
            # 这里用申万行业指数作为代表
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days+30)).strftime('%Y%m%d')

            # 获取行业日线数据
            df = ak.stock_zh_a_hist(symbol=industry_code, period="daily",
                                    start_date=start_date, end_date=end_date, adjust='qfq')
            return df if df is not None and not df.empty else None
        except Exception as e:
            return None

    @classmethod
    def calculate_industry_strength(cls, stock_symbol: str, stock_change: float,
                                    industry: str = None, days: int = 20) -> Dict:
        """
        计算行业相对强弱

        Args:
            stock_symbol: 股票代码
            stock_change: 股票涨跌幅(%)
            industry: 所属行业
            days: 统计天数

        Returns:
            行业相对强弱分析结果
        """
        result = {
            'industry': industry or '未知',
            'industry_strength': 50,  # 行业相对强弱 (0-100)
            'relative_strength': 0,   # 个股相对行业强弱
            'industry_trend': '震荡',  # 行业趋势
            'signal': 'neutral',      # 信号
            'description': ''
        }

        try:
            if not industry or industry == '未知':
                result['description'] = '行业信息未知，无法计算相对强弱'
                return result

            # 获取行业当日涨跌幅（通过同花顺行业板块）
            try:
                # 获取行业板块实时数据
                industry_df = ak.stock_sector_spot()
                spot_data = industry_df[industry_df['板块名称'].str.contains(industry, na=False)]

                if not spot_data.empty:
                    industry_change = float(spot_data.iloc[0]['涨跌幅'])
                    industry_volume = float(spot_data.iloc[0]['成交量'])

                    # 行业相对强弱 = 行业涨跌幅 * 行业动量因子
                    # 动量因子根据成交量判断资金参与度
                    momentum_factor = min(2.0, max(0.5, industry_volume / 1000000))  # 简化计算

                    result['industry_strength'] = min(100, max(0, (industry_change + 10) * 5 * momentum_factor))
                    result['industry_trend'] = '上涨' if industry_change > 2 else '强势' if industry_change > 0 else '下跌' if industry_change < -2 else '弱势'

                    # 个股相对强弱 = 个股涨跌幅 - 行业涨跌幅
                    result['relative_strength'] = stock_change - industry_change

                    # 信号判断
                    if result['relative_strength'] > 3 and industry_change > 0:
                        result['signal'] = 'strong_outperform'
                        result['description'] = f'个股跑赢行业{result["relative_strength"]:.1f}%，行业处于{result["industry_trend"]}'
                    elif result['relative_strength'] > 1 and industry_change > 0:
                        result['signal'] = 'outperform'
                        result['description'] = f'个股小幅跑赢行业{result["relative_strength"]:.1f}%，{result["industry_trend"]}'
                    elif result['relative_strength'] < -3 and industry_change < 0:
                        result['signal'] = 'underperform'
                        result['description'] = f'个股弱于行业{abs(result["relative_strength"]):.1f}%，行业处于{result["industry_trend"]}'
                    elif industry_change > 3 and result['relative_strength'] > -2:
                        result['signal'] = 'follow_up'
                        result['description'] = f'行业{result["industry_trend"]}中，个股跟随上涨'
                    elif industry_change < -3 and result['relative_strength'] > 2:
                        result['signal'] = 'resist_decline'
                        result['description'] = f'行业下跌时个股相对抗跌，展现防御属性'
                    else:
                        result['signal'] = 'neutral'
                        result['description'] = f'个股与行业同步波动，相对强弱{result["relative_strength"]:.1f}%'

                else:
                    result['description'] = f'未找到{industry}板块数据'

            except Exception as e:
                # 如果获取行业数据失败，使用简化逻辑
                if stock_change > 3:
                    result['industry_strength'] = 70
                    result['signal'] = 'strong'
                    result['description'] = '个股涨幅较强，但行业数据获取失败'
                elif stock_change > 0:
                    result['industry_strength'] = 55
                    result['signal'] = 'normal'
                    result['description'] = '个股上涨，行业数据获取失败'
                else:
                    result['industry_strength'] = 45
                    result['signal'] = 'weak'
                    result['description'] = '个股表现弱于大盘，行业数据获取失败'

        except Exception as e:
            result['description'] = f'行业相对强弱分析异常: {str(e)}'

        return result

    @classmethod
    def calculate_industry_score(cls, stock_data: Dict, tech_info: Dict = None) -> float:
        """
        计算行业相对强弱评分 (0-100)

        Args:
            stock_data: 股票数据
            tech_info: 技术指标

        Returns:
            行业评分
        """
        # 获取涨跌幅
        change = 0
        for key in ['区间涨跌幅', '涨跌幅', '区间涨跌幅(%)', '涨跌幅(%)']:
            if key in stock_data:
                try:
                    change = float(stock_data[key])
                    break
                except:
                    pass

        # 获取行业
        industry = None
        for key in ['所属同花顺行业', '所属行业', '行业']:
            if key in stock_data:
                industry = stock_data[key]
                break

        if not industry or industry == 'N/A':
            return 50  # 无行业信息给中等分

        # 计算行业相对强弱
        strength = cls.calculate_industry_strength(
            stock_symbol=stock_data.get('股票代码', ''),
            stock_change=change,
            industry=industry
        )

        # 根据相对强弱和信号计算评分
        score = strength['industry_strength']

        # 根据信号调整分数
        signal_scores = {
            'strong_outperform': 20,   # 大幅跑赢行业
            'outperform': 10,          # 小幅跑赢
            'follow_up': 5,            # 跟随行业上涨
            'resist_decline': 15,      # 抗跌
            'neutral': 0,
            'underperform': -10,       # 弱于行业
            'weak': -5
        }

        score += signal_scores.get(strength['signal'], 0)

        return min(100, max(0, score + 50))  # 基础分50，加上调整


class RiskControlManager:
    """风控建议管理类"""

    # 风险等级定义
    RISK_LEVELS = {
        'low': {'score': (80, 100), 'color': '🟢', 'label': '低风险'},
        'medium': {'score': (60, 80), 'color': '🟡', 'label': '中风险'},
        'high': {'score': (40, 60), 'color': '🟠', 'label': '高风险'},
        'very_high': {'score': (0, 40), 'color': '🔴', 'label': '极高风险'}
    }

    @classmethod
    def calculate_stop_loss_price(cls, current_price: float, tech_info: Dict = None,
                                  volatility: float = 0.05) -> Dict:
        """
        计算止损价位

        Args:
            current_price: 当前价格
            tech_info: 技术指标
            volatility: 波动率

        Returns:
            止损价位建议
        """
        if not tech_info:
            # 简化止损：下跌8%止损
            return {
                'hard_stop_loss': round(current_price * 0.92, 2),
                'soft_stop_loss': round(current_price * 0.95, 2),
                'trailing_stop': round(current_price * 0.93, 2),
                'method': '固定比例法',
                'description': '无技术数据，使用固定比例止损'
            }

        # 技术面止损
        # 1. 布林带下轨止损
        boll_lower = tech_info.get('boll_lower', current_price * 0.95)

        # 2. 均线止损
        ma20 = tech_info.get('ma20', current_price)
        ma60 = tech_info.get('ma60', current_price * 0.9)

        # 3. 前期低点止损
        # 使用近期最低点作为参考

        # 综合计算止损价
        stop_loss_levels = [
            ('布林带止损', boll_lower, 0.25),  # 权重
            ('均线止损(MA20)', ma20, 0.25),
            ('趋势止损(MA60)', ma60, 0.20),
            ('波动止损', current_price * (1 - volatility * 1.5), 0.15),
            ('固定止损-8%', current_price * 0.92, 0.15),
        ]

        weighted_stop = sum(price * weight for _, price, weight in stop_loss_levels)

        return {
            'hard_stop_loss': round(min(boll_lower, current_price * 0.92), 2),
            'soft_stop_loss': round(min(ma20, current_price * 0.95), 2),
            'trailing_stop': round(weighted_stop, 2),
            'boll_stop': round(boll_lower, 2),
            'ma20_stop': round(ma20, 2),
            'ma60_stop': round(ma60, 2),
            'method': '技术面综合法',
            'description': '综合布林带、均线、波动率计算止损'
        }

    @classmethod
    def calculate_take_profit_price(cls, current_price: float, tech_info: Dict = None,
                                   target_ratio: float = 0.15) -> Dict:
        """
        计算止盈价位

        Args:
            current_price: 当前价格
            tech_info: 技术指标
            target_ratio: 目标收益率

        Returns:
            止盈价位建议
        """
        target_price = current_price * (1 + target_ratio)

        if not tech_info:
            # 固定目标止盈
            return {
                'conservative': round(current_price * 1.10, 2),
                'moderate': round(target_price, 2),
                'aggressive': round(current_price * 1.20, 2),
                'method': '固定比例法',
                'description': f'无技术数据，目标收益率{target_ratio*100:.0f}%'
            }

        # 技术面止盈
        boll_upper = tech_info.get('boll_upper', current_price * 1.10)
        ma20 = tech_info.get('ma20', current_price * 1.05)

        # 阻力位计算
        resistance_levels = [
            ('布林带上轨', boll_upper, 0.30),
            ('均线压力(MA20)', ma20, 0.25),
            ('目标涨幅', target_price, 0.25),
            ('前期高点', current_price * 1.12, 0.20),
        ]

        weighted_target = sum(price * weight for _, price, weight in resistance_levels)

        return {
            'conservative': round(min(boll_upper, current_price * 1.08), 2),
            'moderate': round(weighted_target, 2),
            'aggressive': round(max(boll_upper, current_price * 1.15), 2),
            'boll_resistance': round(boll_upper, 2),
            'ma20_resistance': round(ma20, 2),
            'method': '技术面综合法',
            'description': '综合布林带上轨、均线压力位计算止盈'
        }

    @classmethod
    def assess_risk_level(cls, stock_data: Dict, tech_info: Dict = None,
                         fund_info: Dict = None) -> Dict:
        """
        评估股票风险等级

        Args:
            stock_data: 股票数据
            tech_info: 技术指标
            fund_info: 资金指标

        Returns:
            风险评估结果
        """
        risk_score = 50  # 基础分
        risk_factors = []
        risk_warnings = []

        # ========== 技术面风险 ==========
        if tech_info:
            # RSI超买风险
            rsi6 = tech_info.get('rsi6', 50)
            if rsi6 > 85:
                risk_score -= 15
                risk_factors.append(f'RSI严重超买({rsi6:.1f})')
                risk_warnings.append('⚠️ RSI严重超买，注意回调风险')
            elif rsi6 > 75:
                risk_score -= 8
                risk_factors.append(f'RSI超买({rsi6:.1f})')

            # KDJ超买
            if tech_info.get('kdj_overbought'):
                risk_score -= 10
                risk_factors.append('KDJ进入超买区间')

            # 均线空头排列
            if tech_info.get('ma_bearish'):
                risk_score -= 15
                risk_factors.append('均线空头排列')
                risk_warnings.append('⚠️ 均线空头排列，下跌趋势')

            # 布林带上轨压力
            boll_position = tech_info.get('boll_position', 50)
            if boll_position > 90:
                risk_score -= 10
                risk_factors.append(f'股价触及布林带上轨({boll_position:.1f}%)')

            # MACD死叉
            if tech_info.get('macd_dead_cross_days', 0) <= 3:
                risk_score -= 8
                risk_factors.append('MACD刚形成死叉')

            # 量价背离
            vol_price_score = tech_info.get('vol_price_score', 0)
            if vol_price_score < -10:
                risk_score -= 10
                risk_factors.append('量价背离')

        # ========== 基本面风险 ==========
        # 市盈率过高
        pe = stock_data.get('市盈率')
        if pe and pe not in ['N/A', None, '']:
            try:
                pe = float(pe)
                if pe > 100:
                    risk_score -= 10
                    risk_factors.append(f'市盈率过高({pe:.1f})')
                    risk_warnings.append(f'⚠️ 市盈率{pe:.1f}，估值偏高')
                elif pe > 60:
                    risk_score -= 5
                    risk_factors.append(f'市盈率偏高({pe:.1f})')
            except:
                pass

        # 市净率过高
        pb = stock_data.get('市净率')
        if pb and pb not in ['N/A', None, '']:
            try:
                pb = float(pb)
                if pb > 10:
                    risk_score -= 8
                    risk_factors.append(f'市净率过高({pb:.1f})')
            except:
                pass

        # 涨幅过大风险
        change = 0
        for key in ['区间涨跌幅', '涨跌幅']:
            if key in stock_data:
                try:
                    change = float(stock_data[key])
                    break
                except:
                    pass

        if change > 30:
            risk_score -= 15
            risk_factors.append(f'短期涨幅过大({change:.1f}%)')
            risk_warnings.append(f'⚠️ 短期涨幅{change:.1f}%，注意追高风险')
        elif change > 20:
            risk_score -= 8
            risk_factors.append(f'近期涨幅较大({change:.1f}%)')

        # ========== 资金面风险 ==========
        if fund_info:
            # 主力净流出
            main_inflow = fund_info.get('main_inflow', 0)
            if main_inflow < 0:
                risk_score -= 10
                risk_factors.append('主力资金净流出')

        # ========== 确定风险等级 ==========
        risk_level = 'medium'
        for level, info in cls.RISK_LEVELS.items():
            min_score, max_score = info['score']
            if min_score <= risk_score <= max_score:
                risk_level = level
                break

        risk_label = cls.RISK_LEVELS[risk_level]['label']
        risk_color = cls.RISK_LEVELS[risk_level]['color']

        return {
            'risk_score': round(risk_score, 1),
            'risk_level': risk_level,
            'risk_label': risk_label,
            'risk_color': risk_color,
            'risk_factors': risk_factors,
            'risk_warnings': risk_warnings,
            'position_advice': cls._get_position_advice(risk_level, change)
        }

    @classmethod
    def _get_position_advice(cls, risk_level: str, change: float) -> str:
        """获取仓位建议"""
        if change > 25:
            return '建议轻仓或空仓，避免追高'

        advice_map = {
            'low': '建议仓位30-50%',
            'medium': '建议仓位20-30%',
            'high': '建议仓位10-20%',
            'very_high': '建议仓位0-10%或观望'
        }
        return advice_map.get(risk_level, '建议仓位20-30%')

    @classmethod
    def generate_risk_report(cls, stock_data: Dict, tech_info: Dict = None,
                           fund_info: Dict = None, current_price: float = None) -> Dict:
        """
        生成完整风控报告

        Args:
            stock_data: 股票数据
            tech_info: 技术指标
            fund_info: 资金指标
            current_price: 当前价格

        Returns:
            完整风控报告
        """
        symbol = stock_data.get('股票代码', 'N/A')
        name = stock_data.get('股票简称', stock_data.get('名称', 'N/A'))

        # 获取当前价格
        if not current_price and tech_info:
            current_price = tech_info.get('current_price')

        if not current_price:
            current_price = 0

        # 止损止盈计算
        stop_loss = cls.calculate_stop_loss_price(current_price, tech_info)
        take_profit = cls.calculate_take_profit_price(current_price, tech_info)

        # 风险评估
        risk_assessment = cls.assess_risk_level(stock_data, tech_info, fund_info)

        # 风险回报比
        if stop_loss['trailing_stop'] > 0 and current_price > 0:
            risk_ratio = (take_profit['moderate'] - current_price) / (current_price - stop_loss['trailing_stop'])
        else:
            risk_ratio = 1.5

        return {
            'symbol': symbol,
            'name': name,
            'current_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_assessment': risk_assessment,
            'risk_reward_ratio': round(risk_ratio, 2),
            'summary': cls._generate_summary(symbol, name, risk_assessment, stop_loss, take_profit, risk_ratio)
        }

    @classmethod
    def _generate_summary(cls, symbol, name, risk_assessment, stop_loss, take_profit, risk_ratio) -> str:
        """生成风控摘要"""
        risk_color = risk_assessment['risk_color']
        risk_label = risk_assessment['risk_label']

        summary = f"""
【{symbol} {name} 风控摘要】

{risk_color} 风险等级: {risk_label} (评分: {risk_assessment['risk_score']})

📊 风险回报比: 1:{risk_assessment['risk_score']/50:.2f}

💰 建议操作区间:
   - 进场价: {take_profit.get('description', '').split('，')[0] if take_profit.get('description') else ''}
   - 止盈位: 保守{take_profit['conservative']} / 合理{take_profit['moderate']} / 激进{take_profit['aggressive']}
   - 止损位: 硬止损{stop_loss['hard_stop_loss']} / 软止损{stop_loss['soft_stop_loss']}

📋 仓位建议: {risk_assessment['position_advice']}
"""
        if risk_assessment['risk_warnings']:
            summary += "\n⚠️ 风险警示:\n"
            for warning in risk_assessment['risk_warnings']:
                summary += f"   {warning}\n"

        return summary


# 全局实例
industry_relative_strength = IndustryRelativeStrength()
risk_control_manager = RiskControlManager()
