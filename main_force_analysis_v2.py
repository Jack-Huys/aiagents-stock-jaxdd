#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主力选股AI分析整合模块V2 - 优化版
整体批量分析，集成高级多维度筛选策略
"""

from typing import Dict, List, Tuple
import pandas as pd
from main_force_selector_v2 import MainForceStockSelectorV2, AdvancedFilterConfig
from stock_data import StockDataFetcher
from ai_agents import StockAnalysisAgents
from deepseek_client import DeepSeekClient
import time
import json
import config


class MainForceAnalyzerV2:
    """主力选股分析器V2 - 集成高级筛选的批量整体分析"""

    def __init__(self, model=None):
        self.selector = MainForceStockSelectorV2()
        self.fetcher = StockDataFetcher()
        self.model = model or config.DEFAULT_MODEL_NAME
        self.agents = StockAnalysisAgents(model=self.model)
        self.deepseek_client = self.agents.deepseek_client
        self.raw_stocks = None
        self.filtered_stocks = None
        self.advanced_filtered_stocks = None
        self.final_recommendations = []
        self.tech_indicators_cache = {}

    def run_full_analysis(self, start_date: str = None, days_ago: int = None,
                         final_n: int = None, max_range_change: float = None,
                         min_market_cap: float = None, max_market_cap: float = None,
                         strategy_type: str = '稳健型',
                         tech_params: Dict = None,
                         fund_params: Dict = None,
                         fundamental_params: Dict = None,
                         trend_params: Dict = None) -> Dict:
        """
        运行完整的主力选股V2分析流程

        Args:
            start_date: 开始日期，格式如"2025年10月1日"
            days_ago: 距今多少天
            final_n: 最终精选N只
            max_range_change: 最大涨跌幅限制
            min_market_cap: 最小市值限制
            max_market_cap: 最大市值限制
            strategy_type: 策略类型 ('激进型', '稳健型', '价值型', '自定义')
            tech_params: 技术面筛选参数
            fund_params: 资金面筛选参数
            fundamental_params: 基本面筛选参数
            trend_params: 趋势筛选参数

        Returns:
            分析结果字典
        """
        result = {
            'success': False,
            'total_stocks': 0,
            'filtered_stocks': 0,
            'advanced_filtered_stocks': 0,
            'final_recommendations': [],
            'error': None,
            'strategy_type': strategy_type,
            'params': {
                'start_date': start_date,
                'days_ago': days_ago,
                'final_n': final_n,
                'max_range_change': max_range_change,
                'min_market_cap': min_market_cap,
                'max_market_cap': max_market_cap,
                'strategy_type': strategy_type,
                'tech_params': tech_params,
                'fund_params': fund_params,
                'fundamental_params': fundamental_params,
                'trend_params': trend_params
            }
        }

        try:
            print(f"\n{'='*80}")
            print(f"🚀 主力选股V2智能分析系统 - 批量整体分析（优化版）")
            print(f"{'='*80}\n")

            # 获取策略配置
            if strategy_type != '自定义':
                strategy_config = AdvancedFilterConfig.get_strategy(strategy_type)
                tech_params = tech_params or strategy_config.get('tech', {})
                fund_params = fund_params or strategy_config.get('fund', {})
                fundamental_params = fundamental_params or strategy_config.get('fundamental', {})
                trend_params = trend_params or strategy_config.get('trend', {})

            # 步骤1: 获取主力资金净流入前100名股票
            success, raw_data, message = self.selector.get_main_force_stocks(
                start_date=start_date,
                days_ago=days_ago,
                min_market_cap=min_market_cap,
                max_market_cap=max_market_cap
            )

            if not success:
                result['error'] = message
                return result

            result['total_stocks'] = len(raw_data)

            # 步骤2: 基础筛选（涨幅、市值等）
            filtered_data = self.selector.filter_stocks_basic(
                raw_data,
                max_range_change=max_range_change,
                min_market_cap=min_market_cap,
                max_market_cap=max_market_cap
            )

            result['filtered_stocks'] = len(filtered_data) if filtered_data is not None else 0

            if filtered_data is None or filtered_data.empty:
                result['error'] = "基础筛选后没有符合条件的股票"
                return result

            self.filtered_stocks = filtered_data

            # 步骤3: 高级多维度筛选
            print(f"\n{'='*80}")
            print(f"🔍 高级多维度筛选中...")
            print(f"{'='*80}")
            print(f"策略类型: {strategy_type}")
            if strategy_type != '自定义':
                strategy_desc = AdvancedFilterConfig.STRATEGIES[strategy_type].get('description', '')
                print(f"策略描述: {strategy_desc}")

            advanced_filtered = self.selector.filter_stocks_advanced(
                filtered_data,
                tech_params=tech_params,
                fund_params=fund_params,
                fundamental_params=fundamental_params,
                trend_params=trend_params
            )

            # 如果有技术面筛选，应用技术指标筛选
            if tech_params and any(tech_params.values()):
                print(f"\n📊 应用技术指标筛选...")
                # 获取每只股票的技术指标
                for idx, row in advanced_filtered.iterrows():
                    symbol = row.get('股票代码', '')
                    if symbol and symbol not in self.tech_indicators_cache:
                        tech_info = self.selector.get_technical_indicators(symbol)
                        if tech_info:
                            self.tech_indicators_cache[symbol] = tech_info

                # 应用技术面筛选
                advanced_filtered = self.selector.apply_technical_filters(
                    advanced_filtered,
                    tech_params,
                    indicators_cache=self.tech_indicators_cache
                )

            result['advanced_filtered_stocks'] = len(advanced_filtered) if advanced_filtered is not None else 0
            self.advanced_filtered_stocks = advanced_filtered

            if advanced_filtered is None or advanced_filtered.empty:
                result['error'] = "高级筛选后没有符合条件的股票，请尝试放宽筛选条件"
                return result

            # 保存原始数据
            self.raw_stocks = advanced_filtered

            # 步骤4: 多维度评分加权排序
            print(f"\n{'='*80}")
            print(f"📊 对候选股票进行多维度评分排序...")
            print(f"{'='*80}\n")

            from main_force_selector_v2 import MultiDimensionScorer

            scored_df = MultiDimensionScorer.score_and_sort_stocks(
                advanced_filtered,
                tech_indicators_cache=self.tech_indicators_cache,
                fund_indicators_cache=None,  # 资金指标已在筛选时获取
                strategy=strategy_type,
                fundamental_params=fundamental_params,
                trend_params=trend_params,
                top_n=min(len(advanced_filtered), 50)  # 评分前50名用于AI分析
            )

            self.scored_stocks = scored_df

            # 步骤5: 整体数据分析
            print(f"\n{'='*80}")
            print(f"🤖 AI分析师团队开始整体分析...")
            print(f"{'='*80}\n")

            # 准备整体数据摘要（使用评分后的数据）
            overall_summary = self._prepare_overall_summary(scored_df)

            # 三大分析师整体分析
            fund_flow_analysis = self._fund_flow_overall_analysis(scored_df, overall_summary)
            industry_analysis = self._industry_overall_analysis(scored_df, overall_summary)
            fundamental_analysis = self._fundamental_overall_analysis(scored_df, overall_summary)

            # 保存分析报告
            self.fund_flow_analysis = fund_flow_analysis
            self.industry_analysis = industry_analysis
            self.fundamental_analysis = fundamental_analysis

            # 步骤6: 综合决策，精选优质标的
            print(f"\n{'='*80}")
            print(f"👔 资深研究员综合评估并精选标的...")
            print(f"{'='*80}\n")

            final_recommendations = self._select_best_stocks(
                scored_df,
                fund_flow_analysis,
                industry_analysis,
                fundamental_analysis,
                final_n=final_n
            )

            result['final_recommendations'] = final_recommendations
            result['success'] = True

            # 显示最终结果
            self._print_final_recommendations(final_recommendations)

            return result

        except Exception as e:
            result['error'] = f"分析过程出错: {str(e)}"
            import traceback
            traceback.print_exc()
            return result

    def _prepare_overall_summary(self, df: pd.DataFrame) -> str:
        """准备整体数据摘要"""

        summary_lines = []
        summary_lines.append(f"候选股票总数: {len(df)}只")
        summary_lines.append(f"筛选策略: {self._get_strategy_description()}")

        # 主力资金统计
        main_fund_cols = [col for col in df.columns if '主力' in col and '净流入' in col]
        if main_fund_cols:
            col_name = main_fund_cols[0]
            df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
            total_inflow = df[col_name].sum()
            avg_inflow = df[col_name].mean()
            max_inflow = df[col_name].max()
            summary_lines.append(f"主力资金总净流入: {total_inflow/100000000:.2f}亿")
            summary_lines.append(f"平均主力资金净流入: {avg_inflow/100000000:.2f}亿")
            summary_lines.append(f"最大主力资金净流入: {max_inflow/100000000:.2f}亿")

        # 涨跌幅统计
        range_cols = [col for col in df.columns if '涨跌幅' in col]
        if range_cols:
            col_name = range_cols[0]
            df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
            avg_change = df[col_name].mean()
            max_change = df[col_name].max()
            min_change = df[col_name].min()
            summary_lines.append(f"平均涨跌幅: {avg_change:.2f}%")
            summary_lines.append(f"涨跌幅范围: {min_change:.2f}% ~ {max_change:.2f}%")

        # 行业分布
        industry_cols = [col for col in df.columns if '行业' in col]
        if industry_cols:
            col_name = industry_cols[0]
            top_industries = df[col_name].value_counts().head(10)
            summary_lines.append("\n主要行业分布:")
            for industry, count in top_industries.items():
                summary_lines.append(f"  - {industry}: {count}只")

        # 技术指标统计（如果有）
        if self.tech_indicators_cache:
            valid_tech = [v for v in self.tech_indicators_cache.values() if v.get('data_valid')]
            if valid_tech:
                rsi_values = [v.get('rsi6', 0) for v in valid_tech]
                ma_aligned_count = sum(1 for v in valid_tech if v.get('ma_alignment'))
                macd_golden_count = sum(1 for v in valid_tech if v.get('macd_golden_cross_days', 0) > 0)

                summary_lines.append(f"\n技术指标统计（基于{len(valid_tech)}只有效数据）:")
                summary_lines.append(f"  - 平均RSI: {sum(rsi_values)/len(rsi_values):.1f}")
                summary_lines.append(f"  - 均线多头排列: {ma_aligned_count}只")
                summary_lines.append(f"  - MACD金叉: {macd_golden_count}只")

        # 评分统计（如果有）
        if '综合评分' in df.columns:
            summary_lines.append(f"\n多维度评分统计:")
            summary_lines.append(f"  - 平均综合评分: {df['综合评分'].mean():.1f}")
            summary_lines.append(f"  - 最高综合评分: {df['综合评分'].max():.1f}")
            summary_lines.append(f"  - 评分前10名股票:")
            top10 = df.head(10)
            for i, (_, row) in enumerate(top10.iterrows(), 1):
                summary_lines.append(f"    {i}. {row.get('股票代码', 'N/A')} {row.get('股票简称', 'N/A')} - "
                                   f"评分:{row['综合评分']:.1f}")

        return "\n".join(summary_lines)

    def _get_strategy_description(self) -> str:
        """获取策略描述"""
        strategy_desc_map = {
            '激进型': '追求短期爆发，侧重资金面和技术面',
            '稳健型': '追求稳定收益，平衡各维度',
            '价值型': '追求长期价值，侧重基本面',
            '自定义': '自定义筛选参数'
        }
        return strategy_desc_map.get(self._get_current_strategy(), '未知策略')

    def _get_current_strategy(self) -> str:
        """获取当前策略类型"""
        return self._current_strategy if hasattr(self, '_current_strategy') else '稳健型'

    def _fund_flow_overall_analysis(self, df: pd.DataFrame, summary: str) -> str:
        """资金流向整体分析"""

        print("💰 资金流向分析师整体分析中...")

        # 准备数据表格
        data_table = self._prepare_data_table(df, focus='fund_flow')

        prompt = f"""
你是一名资深的资金面分析师，现在需要你从整体角度分析这批主力资金净流入的股票。

【整体数据摘要】
{summary}

【候选股票详细数据】（共{len(df)}只）
{data_table}

【分析任务】
请从资金流向的整体角度进行分析，重点关注：

1. **资金流向特征**
   - 哪些板块/行业资金流入最集中？
   - 主力资金的整体行为特征（大规模建仓/试探性进场/板块轮动）
   - 资金流向与涨跌幅的配合情况

2. **优质标的识别**
   - 从资金面角度，哪些股票最值得关注？
   - 主力资金流入大但涨幅不高的潜力股
   - 资金持续流入且趋势明确的股票

3. **板块热点判断**
   - 当前资金最看好哪些板块？
   - 是否有板块轮动迹象？
   - 新兴热点 vs 传统强势板块

4. **投资建议**
   - 从资金面角度，建议重点关注哪3-5只股票？
   - 理由和风险提示

请给出专业、系统的资金面整体分析报告。
"""

        messages = [
            {"role": "system", "content": "你是资金面分析专家，擅长从整体资金流向中发现投资机会。"},
            {"role": "user", "content": prompt}
        ]

        analysis = self.deepseek_client.call_api(messages, max_tokens=4000)

        print("  ✅ 资金流向整体分析完成")
        time.sleep(1)

        return analysis

    def _industry_overall_analysis(self, df: pd.DataFrame, summary: str) -> str:
        """行业板块整体分析"""

        print("📊 行业板块分析师整体分析中...")

        # 准备数据表格
        data_table = self._prepare_data_table(df, focus='industry')

        prompt = f"""
你是一名资深的行业板块分析师，现在需要你从行业热点和板块轮动角度分析这批股票。

【整体数据摘要】
{summary}

【候选股票详细数据】（共{len(df)}只）
{data_table}

【分析任务】
请从行业板块的整体角度进行分析，重点关注：

1. **热点板块识别**
   - 哪些行业/板块最受资金青睐？
   - 热点板块的持续性如何？
   - 是否有新兴热点正在形成？

2. **板块特征分析**
   - 各板块的涨幅与资金流入匹配度
   - 哪些板块处于启动阶段（资金流入但涨幅不大）
   - 哪些板块可能过热（涨幅高但资金流入减弱）

3. **行业前景评估**
   - 主力资金集中的行业，基本面支撑如何？
   - 政策面、产业面是否有催化因素？
   - 行业竞争格局和龙头地位

4. **优质标的推荐**
   - 从行业板块角度，推荐3-5只最具潜力的股票
   - 推荐理由（行业地位、成长空间、催化因素）

请给出专业、深入的行业板块分析报告。
"""

        messages = [
            {"role": "system", "content": "你是行业板块分析专家，擅长发现市场热点和板块机会。"},
            {"role": "user", "content": prompt}
        ]

        analysis = self.deepseek_client.call_api(messages, max_tokens=4000)

        print("  ✅ 行业板块整体分析完成")
        time.sleep(1)

        return analysis

    def _fundamental_overall_analysis(self, df: pd.DataFrame, summary: str) -> str:
        """财务基本面整体分析"""

        print("📈 财务基本面分析师整体分析中...")

        # 准备数据表格
        data_table = self._prepare_data_table(df, focus='fundamental')

        prompt = f"""
你是一名资深的基本面分析师，现在需要你从财务质量和基本面角度分析这批股票。

【整体数据摘要】
{summary}

【候选股票详细数据】（共{len(df)}只）
{data_table}

【分析任务】
请从财务基本面的整体角度进行分析，重点关注：

1. **财务质量评估**
   - 整体财务指标健康度如何？
   - 哪些股票盈利能力、成长性突出？
   - 是否存在财务风险较大的股票？

2. **估值水平分析**
   - 市盈率、市净率的整体分布
   - 哪些股票估值合理且有成长空间？
   - 高估值是否有业绩支撑？

3. **成长性评估**
   - 营收、净利润增长情况
   - 哪些股票成长性最好？
   - 成长能力评分较高的股票

4. **优质标的筛选**
   - 从基本面角度，推荐3-5只最优质的股票
   - 推荐理由（财务健康、估值合理、成长性好）

请给出专业、详实的基本面分析报告。
"""

        messages = [
            {"role": "system", "content": "你是基本面分析专家，擅长从财务角度评估投资价值。"},
            {"role": "user", "content": prompt}
        ]

        analysis = self.deepseek_client.call_api(messages, max_tokens=4000)

        print("  ✅ 财务基本面整体分析完成")
        time.sleep(1)

        return analysis

    def _prepare_data_table(self, df: pd.DataFrame, focus: str = 'all') -> str:
        """准备数据表格用于AI分析"""

        # 选择关键列
        key_columns = ['股票代码', '股票简称']

        # 根据分析重点添加相关列
        if focus == 'fund_flow' or focus == 'all':
            fund_cols = [col for col in df.columns if '主力' in col or '资金' in col]
            key_columns.extend(fund_cols[:3])

        if focus == 'industry' or focus == 'all':
            industry_cols = [col for col in df.columns if '行业' in col]
            key_columns.extend(industry_cols[:1])

        # 智能匹配区间涨跌幅列
        interval_pct_col = None
        possible_names = [
            '区间涨跌幅:前复权', '区间涨跌幅:前复权(%)', '区间涨跌幅(%)',
            '区间涨跌幅', '涨跌幅:前复权', '涨跌幅:前复权(%)', '涨跌幅(%)', '涨跌幅'
        ]
        for name in possible_names:
            for col in df.columns:
                if name in col:
                    interval_pct_col = col
                    break
            if interval_pct_col:
                break
        if interval_pct_col:
            key_columns.append(interval_pct_col)

        if focus == 'fundamental' or focus == 'all':
            fundamental_cols = [col for col in df.columns if any(
                keyword in col for keyword in ['市盈率', '市净率', '营收', '净利润', '评分', 'ROE', '净资产']
            )]
            key_columns.extend(fundamental_cols[:5])

        # 去重并保持顺序
        seen = set()
        unique_columns = []
        for col in key_columns:
            if col in df.columns and col not in seen:
                seen.add(col)
                unique_columns.append(col)

        # 限制显示前50只股票
        display_df = df[unique_columns].head(50)

        table_str = display_df.to_string(index=False, max_rows=50)

        if len(df) > 50:
            table_str += f"\n... 还有 {len(df) - 50} 只股票未显示"

        return table_str

    def _select_best_stocks(self, df: pd.DataFrame,
                           fund_analysis: str,
                           industry_analysis: str,
                           fundamental_analysis: str,
                           final_n: int = 5) -> List[Dict]:
        """综合三位分析师的意见，精选最优标的"""

        # 准备完整数据表格
        data_table = self._prepare_data_table(df, focus='all')

        # 添加技术指标到数据表格
        tech_table = self._prepare_tech_table(df)

        prompt = f"""
你是一名资深股票研究员，具有20年以上的投资研究经验。现在需要你综合四位分析师的意见，
从{len(df)}只候选股票中精选出{final_n}只最具投资价值的优质标的。

【候选股票数据】
{data_table}

【技术指标数据】
{tech_table}

【资金流向分析师观点】
{fund_analysis}

【行业板块分析师观点】
{industry_analysis}

【财务基本面分析师观点】
{fundamental_analysis}

【筛选标准 - V2优化版】
1. **主力资金**: 主力资金净流入较多，显示机构看好
2. **涨幅适中**: 区间涨跌幅适中（避免追高），还有上涨空间
3. **技术面健康**: RSI在合理区间，均线多头排列，MACD金叉等
4. **行业热点**: 所属行业有发展前景，是市场热点
5. **基本面良好**: 财务指标健康，盈利能力强，估值合理
6. **综合平衡**: 资金、技术、行业、基本面四方面都不错

【任务要求】
综合四位分析师的观点，精选出{final_n}只最优标的。

对于每只精选股票，请提供：
1. **股票代码和名称**
2. **核心推荐理由**（3-5条，综合资金、技术、行业、基本面）
3. **投资亮点**（最突出的优势）
4. **风险提示**（需要注意的风险）
5. **建议仓位**（如20-30%）
6. **投资周期**（短期/中期/长期）

请按以下JSON格式输出（只输出JSON，不要其他内容）：
```json
{{
  "recommendations": [
    {{
      "rank": 1,
      "symbol": "股票代码",
      "name": "股票名称",
      "reasons": [
        "理由1：资金面角度",
        "理由2：技术面角度",
        "理由3：行业板块角度",
        "理由4：基本面角度"
      ],
      "highlights": "投资亮点描述",
      "risks": "风险提示",
      "position": "建议仓位",
      "investment_period": "投资周期"
    }}
  ]
}}
```

注意：
- 必须严格按照JSON格式输出
- 推荐数量为{final_n}只
- 按投资价值从高到低排序
- 理由要具体、有说服力，体现四位分析师的综合观点
"""

        try:
            print("  🔍 正在综合评估并精选标的...")

            messages = [
                {"role": "system", "content": "你是资深股票研究员，擅长综合多维度分析做出投资决策。"},
                {"role": "user", "content": prompt}
            ]

            response = self.deepseek_client.call_api(messages, max_tokens=4000)

            # 解析JSON响应
            import re

            # 提取JSON部分
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response

            result = json.loads(json_str)
            recommendations = result.get('recommendations', [])

            # 补充详细数据、技术指标和评分
            for rec in recommendations:
                symbol = rec['symbol']
                stock_data = df[df['股票代码'] == symbol]
                if not stock_data.empty:
                    rec['stock_data'] = stock_data.iloc[0].to_dict()
                    # 添加技术指标
                    if symbol in self.tech_indicators_cache:
                        rec['tech_indicators'] = self.tech_indicators_cache[symbol]
                    # 添加评分信息
                    score_cols = ['综合评分', '技术面评分', '资金面评分', '基本面评分', '趋势面评分',
                                 '行业评分', '问财评分', '风控评分']
                    for col in score_cols:
                        if col in stock_data.iloc[0].to_dict():
                            rec[col] = stock_data.iloc[0].to_dict().get(col)
                    # 添加风控报告
                    if '评分明细' in stock_data.iloc[0].to_dict():
                        rec['risk_report'] = stock_data.iloc[0].to_dict().get('评分明细', {}).get('risk_report')

            return recommendations

        except Exception as e:
            print(f"  ❌ JSON解析失败，使用备选方案: {e}")

            # 降级方案：按主力资金排序返回前N个
            main_fund_cols = [col for col in df.columns if '主力' in col and '净流入' in col]
            if main_fund_cols:
                col_name = main_fund_cols[0]
                df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
                sorted_df = df.nlargest(final_n, col_name)
            else:
                sorted_df = df.head(final_n)

            recommendations = []
            for i, (idx, row) in enumerate(sorted_df.iterrows(), 1):
                symbol = row.get('股票代码', 'N/A')
                recommendations.append({
                    'rank': i,
                    'symbol': symbol,
                    'name': row.get('股票简称', row.get('名称', 'N/A')),
                    'reasons': [
                        f"主力资金净流入较多",
                        f"所属行业: {row.get('所属同花顺行业', 'N/A')}",
                        f"涨跌幅适中"
                    ],
                    'highlights': '主力资金持续关注',
                    'risks': '需关注后续走势',
                    'position': '15-25%',
                    'investment_period': '中短期',
                    'stock_data': row.to_dict(),
                    'tech_indicators': self.tech_indicators_cache.get(symbol) if symbol in self.tech_indicators_cache else None
                })

            return recommendations

    def _prepare_tech_table(self, df: pd.DataFrame) -> str:
        """准备技术指标表格"""
        if not self.tech_indicators_cache:
            return "暂无技术指标数据"

        lines = []
        lines.append("\n【技术指标数据】")

        for idx, row in df.iterrows():
            symbol = row.get('股票代码', '')
            if symbol in self.tech_indicators_cache:
                tech = self.tech_indicators_cache[symbol]
                name = row.get('股票简称', row.get('名称', ''))
                rsi = tech.get('rsi6', 0)
                kdj_k = tech.get('kdj_k', 0)
                ma_align = "是" if tech.get('ma_alignment') else "否"
                macd_golden = tech.get('macd_golden_cross_days', 0)
                kdj_golden = tech.get('kdj_golden_cross_days', 0)
                boll_support = "是" if tech.get('boll_mid_support') else "否"
                vol_ratio = tech.get('volume_ratio', 0)
                vol_price = tech.get('vol_price_score', 0)

                lines.append(f"{symbol} {name}: RSI={rsi:.1f}, KDJ_K={kdj_k:.1f}, 均线多头={ma_align}, "
                           f"MACD金叉={macd_golden}日前, KDJ金叉={kdj_golden}日前, 布林支撑={boll_support}, "
                           f"量比={vol_ratio:.1f}, 量价={vol_price:.0f}")

        return "\n".join(lines[:25])  # 限制行数

    def _print_final_recommendations(self, recommendations: List[Dict]):
        """打印最终推荐结果"""
        if not recommendations:
            print("❌ 未能生成推荐结果")
            return

        print(f"\n{'='*80}")
        print(f"⭐ 最终精选推荐 ({len(recommendations)}只) - V2优化版")
        print(f"{'='*80}\n")

        for rec in recommendations:
            print(f"【第{rec['rank']}名】{rec['symbol']} - {rec['name']}")
            print(f"{'-'*60}")

            print(f"📌 推荐理由:")
            for reason in rec.get('reasons', []):
                print(f"   • {reason}")

            print(f"\n💡 投资亮点: {rec.get('highlights', 'N/A')}")
            print(f"⚠️  风险提示: {rec.get('risks', 'N/A')}")
            print(f"📊 建议仓位: {rec.get('position', 'N/A')}")
            print(f"⏰ 投资周期: {rec.get('investment_period', 'N/A')}")

            # 显示技术指标
            if 'tech_indicators' in rec and rec['tech_indicators']:
                tech = rec['tech_indicators']
                print(f"📈 技术指标: RSI={tech.get('rsi6', 'N/A'):.1f}, MACD金叉={tech.get('macd_golden_cross_days', 0)}日前")

            print(f"{'='*80}\n")


# 全局实例
main_force_analyzer_v2 = MainForceAnalyzerV2()