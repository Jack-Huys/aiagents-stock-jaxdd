#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主力选股UI模块V2 - 优化版
集成高级多维度筛选策略
"""

import streamlit as st
from datetime import datetime, timedelta
from main_force_analysis_v2 import MainForceAnalyzerV2
from main_force_selector_v2 import AdvancedFilterConfig
from main_force_pdf_generator import display_report_download_section
from main_force_history_ui import display_batch_history
import pandas as pd


def display_main_force_selector_v2():
    """显示主力选股V2界面"""

    # 检查是否触发批量分析
    if st.session_state.get('main_force_batch_trigger_v2'):
        run_main_force_batch_analysis_v2()
        return

    # 检查是否查看历史记录
    if st.session_state.get('main_force_view_history'):
        display_batch_history()
        return

    # 页面标题和历史记录按钮
    col_title, col_history, col_v1 = st.columns([3, 1, 1])
    with col_title:
        st.markdown("## 🎯 主力选股V2 - 多维度智能筛选（优化版）")
    with col_history:
        st.write("")
        if st.button("📚 批量分析历史", width='content'):
            st.session_state.main_force_view_history = True
            st.rerun()
    with col_v1:
        st.write("")
        if st.button("📋 V1版本", width='content', help="返回原始版本"):
            st.session_state.show_main_force = True
            for key in ['show_history', 'show_monitor', 'show_config', 'show_sector_strategy',
                       'show_longhubang', 'show_portfolio', 'show_main_force_v2', 'show_low_price_bull', 'show_news_flow', 'show_macro_analysis']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    st.markdown("---")

    st.markdown("""
    ### 功能说明

    V2版本在原版基础上增加了多维度高级筛选功能：

    1. **数据获取**: 使用问财获取指定日期以来主力资金净流入前100名股票
    2. **基础筛选**: 过滤掉涨幅过高、市值不符的股票
    3. **高级筛选**: 技术面、资金面、基本面、趋势四维度智能筛选
    4. **AI分析**: 调用资金流向、行业板块、财务基本面三大分析师团队
    5. **综合决策**: 资深研究员综合评估，精选3-5只优质标的

    **筛选标准**:
    - ✅ 主力资金净流入较多
    - ✅ 区间涨跌幅适中（避免追高）
    - ✅ 技术面健康（RSI、MACD、均线多头等）
    - ✅ 资金面强势（连续净流入、主力占比高等）
    - ✅ 财务基本面良好（ROE、成长性、估值等）
    - ✅ 趋势向上（年线支撑、筹码集中等）
    """)

    st.markdown("---")

    # ========== 策略选择 ==========
    st.markdown("### 📊 选择筛选策略")

    strategy_type = st.selectbox(
        "筛选策略类型",
        options=['稳健型', '激进型', '价值型', '自定义'],
        index=0,
        help="""
        - **稳健型**: 追求稳定收益，平衡各维度（默认推荐）
        - **激进型**: 追求短期爆发，侧重资金面和技术面
        - **价值型**: 追求长期价值，侧重基本面
        - **自定义**: 自定义各维度筛选参数
        """
    )

    # 显示策略描述
    strategy_info = AdvancedFilterConfig.get_strategy(strategy_type)
    st.info(f"**{strategy_type}**: {strategy_info.get('description', '')}")

    # ========== 时间范围和数量选择 ==========
    col1, col2, col3 = st.columns(3)

    with col1:
        date_option = st.selectbox(
            "选择时间区间",
            ["最近3个月", "最近6个月", "最近1年", "自定义日期"]
        )

        if date_option == "最近3个月":
            days_ago = 90
            start_date = None
        elif date_option == "最近6个月":
            days_ago = 180
            start_date = None
        elif date_option == "最近1年":
            days_ago = 365
            start_date = None
        else:
            custom_date = st.date_input(
                "选择开始日期",
                value=datetime.now() - timedelta(days=90)
            )
            start_date = f"{custom_date.year}年{custom_date.month}月{custom_date.day}日"
            days_ago = None

    with col2:
        final_n = st.slider(
            "最终精选数量",
            min_value=3,
            max_value=10,
            value=5,
            step=1,
            help="最终推荐的股票数量"
        )

    with col3:
        st.info("💡 V2版本增加多维度筛选，成功率更高")

    st.markdown("---")

    # ========== 基础筛选参数 ==========
    with st.expander("⚙️ 基础筛选参数", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            max_change = st.number_input(
                "最大涨跌幅(%)",
                min_value=5.0,
                max_value=200.0,
                value=30.0,
                step=5.0,
                help="过滤掉涨幅过高的股票，避免追高"
            )

        with col2:
            min_cap = st.number_input(
                "最小市值(亿)",
                min_value=10.0,
                max_value=500.0,
                value=50.0,
                step=10.0
            )

        with col3:
            max_cap = st.number_input(
                "最大市值(亿)",
                min_value=50.0,
                max_value=50000.0,
                value=5000.0,
                step=100.0
            )

    # ========== 高级筛选参数 ==========
    with st.expander("🔍 高级筛选参数（V2新增）", expanded=True):

        st.markdown("##### 📊 技术面筛选")

        # 根据策略预填充参数
        default_tech = strategy_info.get('tech', {})

        col1, col2, col3 = st.columns(3)
        with col1:
            rsi_min = st.number_input(
                "RSI最低值",
                min_value=0.0,
                max_value=100.0,
                value=float(default_tech.get('rsi_min', 30)),
                help="RSI低于此值表示超卖"
            )
            rsi_max = st.number_input(
                "RSI最高值",
                min_value=0.0,
                max_value=100.0,
                value=float(default_tech.get('rsi_max', 80)),
                help="RSI高于此值表示超买"
            )

        with col2:
            macd_golden = st.checkbox(
                "需要MACD金叉",
                value=default_tech.get('macd_golden_cross', False),
                help="DIF上穿DEA"
            )
            if macd_golden:
                macd_days = st.number_input(
                    "MACD金叉天数内",
                    min_value=1.0,
                    max_value=20.0,
                    value=float(default_tech.get('macd_golden_cross_days', 5)),
                    help="在N日内出现金叉"
                )
            else:
                macd_days = 0

        with col3:
            ma_alignment = st.checkbox(
                "需要均线多头排列",
                value=default_tech.get('ma_alignment', False),
                help="MA5>MA10>MA20>MA60"
            )
            price_breakout = st.checkbox(
                "突破20日均线",
                value=default_tech.get('price_breakout_20ma', False)
            )
            boll_support = st.checkbox(
                "布林带中轨支撑",
                value=default_tech.get('boll_mid_support', False)
            )

        st.markdown("---")
        st.markdown("##### 💰 资金面筛选")

        default_fund = strategy_info.get('fund', {})

        col1, col2, col3 = st.columns(3)
        with col1:
            main_ratio_min = st.number_input(
                "主力净流入占比(%)",
                min_value=0.0,
                max_value=100.0,
                value=float(default_fund.get('main_fund_ratio_min', 15)),
                help="主力净流入占成交额比例"
            )
            consecutive_days = st.number_input(
                "连续净流入天数",
                min_value=0.0,
                max_value=20.0,
                value=float(default_fund.get('consecutive_days_min', 3)),
                help="连续净流入的最少天数"
            )

        with col2:
            super_large = st.checkbox(
                "超大单净流入",
                value=default_fund.get('super_large_inflow', False),
                help="需要超大单净流入"
            )
            north_bound = st.checkbox(
                "北向资金增持",
                value=default_fund.get('north_bound_increase', False),
                help="需要北向资金增持"
            )

        with col3:
            st.write("")  # 占位

        st.markdown("---")
        st.markdown("##### 📈 基本面筛选")

        default_fundamental = strategy_info.get('fundamental', {})

        col1, col2, col3 = st.columns(3)
        with col1:
            roe_min = st.number_input(
                "ROE最低值(%)",
                min_value=0.0,
                max_value=50.0,
                value=float(default_fundamental.get('roe_min', 8)),
                help="净资产收益率最低要求"
            )
            profit_growth = st.number_input(
                "净利润增长最低(%)",
                min_value=-100.0,
                max_value=1000.0,
                value=float(default_fundamental.get('profit_growth_min', 0)),
                help="净利润同比增长最低要求"
            )

        with col2:
            debt_ratio = st.number_input(
                "资产负债率最高(%)",
                min_value=0.0,
                max_value=100.0,
                value=float(default_fundamental.get('debt_ratio_max', 65)),
                help="资产负债率最高限制"
            )
            peg_max = st.number_input(
                "PEG最高值",
                min_value=0.0,
                max_value=20.0,
                value=float(default_fundamental.get('peg_max', 2)),
                step=0.1,
                help="PEG = 市盈率/增长率，越低越有投资价值"
            )

        with col3:
            dividend_min = st.number_input(
                "股息率最低(%)",
                min_value=0.0,
                max_value=20.0,
                value=float(default_fundamental.get('dividend_min', 1)),
                step=0.1,
                help="股息率最低要求"
            )

        st.markdown("---")
        st.markdown("##### 📉 趋势筛选")

        default_trend = strategy_info.get('trend', {})

        col1, col2, col3 = st.columns(3)
        with col1:
            amplitude_min = st.number_input(
                "振幅最低(%)",
                min_value=0.0,
                max_value=50.0,
                value=float(default_trend.get('amplitude_min', 8)),
                help="日均振幅最低要求"
            )
            amplitude_max = st.number_input(
                "振幅最高(%)",
                min_value=0.0,
                max_value=100.0,
                value=float(default_trend.get('amplitude_max', 35)),
                help="日均振幅最高限制"
            )

        with col2:
            above_year_ma = st.checkbox(
                "股价在年线上方",
                value=default_trend.get('above_year_ma', False),
                help="股价在250日均线上方"
            )
            chip_concentration = st.checkbox(
                "筹码集中度提升",
                value=default_trend.get('chip_concentration', False),
                help="筹码集中度提升"
            )

        with col3:
            st.write("")

    st.markdown("---")

    # 开始分析按钮
    if st.button("🚀 开始主力选股V2", type="primary", width='content'):

        # 整理高级筛选参数
        tech_params = {
            'rsi_min': rsi_min,
            'rsi_max': rsi_max,
            'macd_golden_cross': macd_golden,
            'macd_golden_cross_days': macd_days,
            'ma_alignment': ma_alignment,
            'price_breakout_20ma': price_breakout,
            'boll_mid_support': boll_support,
            'amplitude_min': amplitude_min,
            'amplitude_max': amplitude_max,
        }

        fund_params = {
            'main_fund_ratio_min': main_ratio_min,
            'consecutive_days_min': consecutive_days,
            'super_large_inflow': super_large,
            'north_bound_increase': north_bound,
        }

        fundamental_params = {
            'roe_min': roe_min,
            'profit_growth_min': profit_growth,
            'debt_ratio_max': debt_ratio,
            'peg_max': peg_max,
            'dividend_min': dividend_min,
        }

        trend_params = {
            'amplitude_min': amplitude_min,
            'amplitude_max': amplitude_max,
            'above_year_ma': above_year_ma,
            'chip_concentration': chip_concentration,
        }

        with st.spinner("正在获取数据并分析，这可能需要几分钟..."):

            # 创建分析器
            analyzer = MainForceAnalyzerV2()

            # 运行分析
            result = analyzer.run_full_analysis(
                start_date=start_date,
                days_ago=days_ago,
                final_n=final_n,
                max_range_change=max_change,
                min_market_cap=min_cap,
                max_market_cap=max_cap,
                strategy_type=strategy_type,
                tech_params=tech_params,
                fund_params=fund_params,
                fundamental_params=fundamental_params,
                trend_params=trend_params
            )

            # 保存结果到session_state
            st.session_state.main_force_result_v2 = result
            st.session_state.main_force_analyzer_v2 = analyzer

        # 显示结果
        if result['success']:
            st.success(f"✅ 分析完成！共筛选出 {len(result['final_recommendations'])} 只优质标的")
            st.rerun()
        else:
            st.error(f"❌ 分析失败: {result.get('error', '未知错误')}")

    # 显示分析结果
    if 'main_force_result_v2' in st.session_state:
        result = st.session_state.main_force_result_v2

        if result['success']:
            display_analysis_results_v2(result, st.session_state.get('main_force_analyzer_v2'))


def display_analysis_results_v2(result: dict, analyzer):
    """显示V2分析结果"""

    st.markdown("---")
    st.markdown("## 📊 V2分析结果")

    # 统计信息
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("获取股票数", result['total_stocks'])

    with col2:
        st.metric("基础筛选后", result['filtered_stocks'])

    with col3:
        st.metric("高级筛选后", result.get('advanced_filtered_stocks', result['filtered_stocks']))

    with col4:
        st.metric("最终推荐", len(result['final_recommendations']))

    # 显示策略信息
    st.info(f"🎯 使用策略: {result.get('strategy_type', '未知')} | 高级筛选进一步过滤了不合格股票")

    st.markdown("---")

    # 显示AI分析师完整报告
    if analyzer and hasattr(analyzer, 'fund_flow_analysis'):
        display_analyst_reports_v2(analyzer)

    st.markdown("---")

    # 显示推荐股票
    if result['final_recommendations']:
        st.markdown("### ⭐ 精选推荐")

        for rec in result['final_recommendations']:
            with st.expander(
                f"【第{rec['rank']}名】{rec['symbol']} - {rec['name']}",
                expanded=(rec['rank'] <= 3)
            ):
                display_recommendation_detail_v2(rec)

    # 显示候选股票列表
    display_df = None
    if analyzer and hasattr(analyzer, 'scored_stocks') and analyzer.scored_stocks is not None and not analyzer.scored_stocks.empty:
        display_stocks = analyzer.scored_stocks
    elif analyzer and analyzer.raw_stocks is not None and not analyzer.raw_stocks.empty:
        display_stocks = analyzer.raw_stocks
    else:
        display_stocks = None

    if display_stocks is not None:
        st.markdown("---")
        st.markdown("### 📋 候选股票列表（多维度评分排序）")

        # 选择关键列显示
        display_cols = ['股票代码', '股票简称', '综合评分']

        # 添加各维度评分列
        for col in ['技术面评分', '资金面评分', '基本面评分', '趋势面评分', '行业评分', '问财评分', '风控评分']:
            if col in display_stocks.columns:
                display_cols.append(col)

        # 添加行业列
        industry_cols = [col for col in display_stocks.columns if '行业' in col]
        if industry_cols:
            display_cols.append(industry_cols[0])

        # 添加主力资金列
        main_fund_col = None
        main_fund_patterns = [
            '区间主力资金流向', '区间主力资金净流入', '主力资金流向',
            '主力资金净流入', '主力净流入', '主力资金'
        ]
        for pattern in main_fund_patterns:
            matching = [col for col in display_stocks.columns if pattern in col]
            if matching:
                main_fund_col = matching[0]
                break
        if main_fund_col:
            display_cols.append(main_fund_col)

        # 添加涨跌幅列
        interval_pct_col = None
        interval_pct_patterns = [
            '区间涨跌幅:前复权', '区间涨跌幅:前复权(%)', '区间涨跌幅(%)',
            '区间涨跌幅', '涨跌幅:前复权', '涨跌幅:前复权(%)', '涨跌幅(%)', '涨跌幅'
        ]
        for pattern in interval_pct_patterns:
            matching = [col for col in display_stocks.columns if pattern in col]
            if matching:
                interval_pct_col = matching[0]
                break
        if interval_pct_col:
            display_cols.append(interval_pct_col)

        # 添加市值、市盈率、市净率
        for col_name in ['总市值', '市盈率', '市净率']:
            matching_cols = [col for col in display_stocks.columns if col_name in col]
            if matching_cols:
                display_cols.append(matching_cols[0])

        # 选择存在的列
        final_cols = [col for col in display_cols if col in display_stocks.columns]

        # 显示DataFrame
        display_df = display_stocks[final_cols].copy()
        st.dataframe(display_df, width='content', height=400)

        # 下载按钮
        csv = display_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 下载候选列表CSV",
            data=csv,
            file_name=f"main_force_stocks_v2_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

        # 批量分析功能区
        st.markdown("---")

        col_batch1, col_batch2, col_batch3 = st.columns([2, 1, 1])
        with col_batch1:
            st.markdown("#### 🚀 批量深度分析")
            st.caption("对主力资金净流入TOP股票进行完整的AI团队分析")

        with col_batch2:
            batch_count = st.selectbox(
                "分析数量",
                options=[10, 20, 30, 50],
                index=1,
                help="选择分析主力资金净流入前N只股票"
            )

        with col_batch3:
            st.write("")
            if st.button("🚀 开始批量分析", type="primary", width='content'):
                # 准备数据
                df_sorted = analyzer.raw_stocks.copy()

                if main_fund_col:
                    df_sorted[main_fund_col] = pd.to_numeric(df_sorted[main_fund_col], errors='coerce')
                    df_sorted = df_sorted.sort_values(by=main_fund_col, ascending=False)

                # 提取股票代码
                raw_codes = df_sorted.head(batch_count)['股票代码'].tolist()
                stock_codes = []
                for code in raw_codes:
                    if isinstance(code, str):
                        clean_code = code.split('.')[0] if '.' in code else code
                        stock_codes.append(clean_code)
                    else:
                        stock_codes.append(str(code))

                st.session_state.main_force_batch_codes = stock_codes
                st.session_state.main_force_batch_trigger_v2 = True
                st.rerun()

    # 显示PDF报告下载区域
    if analyzer and result:
        display_report_download_section(analyzer, result)


def display_recommendation_detail_v2(rec: dict):
    """显示V2单个推荐股票的详细信息"""

    col1, col2 = st.columns([1, 1])

    with col1:
        # 显示综合评分
        score = rec.get('total_score', rec.get('综合评分', 'N/A'))
        if score != 'N/A':
            st.markdown(f"#### 📊 综合评分: **{score:.1f}**")

        # 显示各维度评分
        if 'tech_score' in rec or '技术面评分' in rec:
            st.markdown("##### 各维度评分:")
            cols = st.columns(7)
            scores_data = [
                ('技术面', rec.get('tech_score', rec.get('技术面评分', 'N/A'))),
                ('资金面', rec.get('fund_score', rec.get('资金面评分', 'N/A'))),
                ('基本面', rec.get('fundamental_score', rec.get('基本面评分', 'N/A'))),
                ('趋势面', rec.get('trend_score', rec.get('趋势面评分', 'N/A'))),
                ('行业', rec.get('industry_score', rec.get('行业评分', 'N/A'))),
                ('问财', rec.get('wencai_score', rec.get('问财评分', 'N/A'))),
                ('风控', rec.get('risk_score', rec.get('风控评分', 'N/A'))),
            ]
            for col, (name, val) in zip(cols, scores_data):
                if val != 'N/A':
                    col.metric(name, f"{val:.1f}")

        st.markdown("#### 📌 推荐理由")
        for reason in rec.get('reasons', []):
            st.markdown(f"- {reason}")

        st.markdown("#### 💡 投资亮点")
        st.info(rec.get('highlights', 'N/A'))

    with col2:
        st.markdown("#### 📊 投资建议")
        st.markdown(f"**建议仓位**: {rec.get('position', 'N/A')}")
        st.markdown(f"**投资周期**: {rec.get('investment_period', 'N/A')}")

        st.markdown("#### ⚠️ 风险提示")
        st.warning(rec.get('risks', 'N/A'))

    # 显示技术指标
    if 'tech_indicators' in rec and rec['tech_indicators']:
        st.markdown("---")
        st.markdown("#### 📈 技术指标")
        tech = rec['tech_indicators']

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            rsi = tech.get('rsi6', 0)
            st.metric("RSI(6)", f"{rsi:.1f}")
        with col2:
            ma_align = "是" if tech.get('ma_alignment') else "否"
            st.metric("均线多头", ma_align)
        with col3:
            macd_days = tech.get('macd_golden_cross_days', 0)
            st.metric("MACD金叉", f"{macd_days}日前" if macd_days > 0 else "否")
        with col4:
            boll = "是" if tech.get('boll_mid_support') else "否"
            st.metric("布林支撑", boll)

        # KDJ指标
        st.markdown("**KDJ指标:**")
        col1, col2, col3 = st.columns(3)
        with col1:
            kdj_k = tech.get('kdj_k', 0)
            st.metric("K值", f"{kdj_k:.1f}")
        with col2:
            kdj_d = tech.get('kdj_d', 0)
            st.metric("D值", f"{kdj_d:.1f}")
        with col3:
            kdj_j = tech.get('kdj_j', 0)
            st.metric("J值", f"{kdj_j:.1f}")

        # 量价分析
        st.markdown("**量价配合:**")
        col1, col2, col3 = st.columns(3)
        with col1:
            vol_ratio = tech.get('volume_ratio', 0)
            st.metric("量比", f"{vol_ratio:.2f}")
        with col2:
            vol_price = tech.get('vol_price_score', 0)
            vol_status = "量增价涨" if vol_price > 10 else "量缩价稳" if vol_price > 0 else "量价背离"
            st.metric("量价状态", vol_status)
        with col3:
            obv_trend = tech.get('obv_trend', 0)
            obv_status = "OBV上升" if obv_trend > 0 else "OBV下降" if obv_trend < 0 else "OBV平稳"
            st.metric("OBV趋势", obv_status)

    # 显示风控建议
    if 'risk_report' in rec and rec['risk_report']:
        st.markdown("---")
        st.markdown("#### 🛡️ 风控建议")
        risk = rec['risk_report']
        risk_assess = risk.get('risk_assessment', {})

        # 风险等级
        risk_color = risk_assess.get('risk_color', '🟡')
        risk_label = risk_assess.get('risk_label', '中风险')
        risk_score = risk_assess.get('risk_score', 50)
        st.markdown(f"{risk_color} **风险等级: {risk_label}** (评分: {risk_score:.1f})")

        # 止损止盈建议
        stop_loss = risk.get('stop_loss', {})
        take_profit = risk.get('take_profit', {})

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**止损建议:**")
            st.info(f"硬止损: {stop_loss.get('hard_stop_loss', 'N/A')}")
            st.info(f"软止损: {stop_loss.get('soft_stop_loss', 'N/A')}")
        with col2:
            st.markdown("**止盈建议:**")
            st.success(f"保守: {take_profit.get('conservative', 'N/A')}")
            st.success(f"合理: {take_profit.get('moderate', 'N/A')}")
        with col3:
            st.markdown("**风险回报比:**")
            rr = risk.get('risk_reward_ratio', 1.5)
            st.metric("盈亏比", f"1:{rr:.2f}")

        # 风险因素
        risk_factors = risk_assess.get('risk_factors', [])
        if risk_factors:
            st.markdown("**风险因素:**")
            for factor in risk_factors:
                st.warning(f"- {factor}")

        # 仓位建议
        position_advice = risk_assess.get('position_advice', '')
        if position_advice:
            st.info(f"📊 {position_advice}")

    # 显示股票详细数据
    if 'stock_data' in rec:
        st.markdown("---")
        st.markdown("#### 📊 股票详细数据")

        stock_data = rec['stock_data']

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("股票代码", stock_data.get('股票代码', 'N/A'))

            industry_keys = [k for k in stock_data.keys() if '行业' in k]
            if industry_keys:
                st.metric("所属行业", stock_data.get(industry_keys[0], 'N/A'))

        with col2:
            fund_keys = [k for k in stock_data.keys() if '主力' in k and '净流入' in k]
            if fund_keys:
                fund_value = stock_data.get(fund_keys[0], 'N/A')
                if isinstance(fund_value, (int, float)):
                    st.metric("主力资金净流入", f"{fund_value/100000000:.2f}亿")
                else:
                    st.metric("主力资金净流入", str(fund_value))

        with col3:
            change_keys = [k for k in stock_data.keys() if '涨跌幅' in k]
            if change_keys:
                change_value = stock_data.get(change_keys[0], 'N/A')
                if isinstance(change_value, (int, float)):
                    st.metric("区间涨跌幅", f"{change_value:.2f}%")
                else:
                    st.metric("区间涨跌幅", str(change_value))


def display_analyst_reports_v2(analyzer):
    """显示V2 AI分析师完整报告"""

    st.markdown("### 🤖 AI分析师团队完整报告")

    tab1, tab2, tab3 = st.tabs(["💰 资金流向分析", "📊 行业板块分析", "📈 财务基本面分析"])

    with tab1:
        st.markdown("#### 💰 资金流向分析师报告")
        st.markdown("---")
        if hasattr(analyzer, 'fund_flow_analysis') and analyzer.fund_flow_analysis:
            st.markdown(analyzer.fund_flow_analysis)
        else:
            st.info("暂无资金流向分析报告")

    with tab2:
        st.markdown("#### 📊 行业板块及市场热点分析师报告")
        st.markdown("---")
        if hasattr(analyzer, 'industry_analysis') and analyzer.industry_analysis:
            st.markdown(analyzer.industry_analysis)
        else:
            st.info("暂无行业板块分析报告")

    with tab3:
        st.markdown("#### 📈 财务基本面分析师报告")
        st.markdown("---")
        if hasattr(analyzer, 'fundamental_analysis') and analyzer.fundamental_analysis:
            st.markdown(analyzer.fundamental_analysis)
        else:
            st.info("暂无财务基本面分析报告")


def run_main_force_batch_analysis_v2():
    """执行主力选股V2 TOP股票批量分析"""
    import time
    import re

    st.markdown("## 🚀 主力选股V2批量深度分析")
    st.markdown("---")

    # 检查是否已有分析结果
    if st.session_state.get('main_force_batch_results'):
        display_main_force_batch_results_v2(st.session_state.main_force_batch_results)

        col_back, col_clear = st.columns(2)
        with col_back:
            if st.button("🔙 返回主力选股V2", width='content'):
                for key in ['main_force_batch_trigger_v2', 'main_force_batch_codes',
                           'main_force_batch_results']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

        with col_clear:
            if st.button("🔄 重新分析", width='content'):
                if 'main_force_batch_results' in st.session_state:
                    del st.session_state.main_force_batch_results
                st.rerun()

        return

    # 获取股票代码列表
    stock_codes = st.session_state.get('main_force_batch_codes', [])

    if not stock_codes:
        st.error("未找到股票代码列表")
        if 'main_force_batch_trigger_v2' in st.session_state:
            del st.session_state.main_force_batch_trigger_v2
        return

    st.info(f"即将分析 {len(stock_codes)} 只股票：{', '.join(stock_codes[:10])}{'...' if len(stock_codes) > 10 else ''}")

    if st.button("🔙 取消返回", type="secondary"):
        for key in ['main_force_batch_trigger_v2', 'main_force_batch_codes']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        analysis_mode = st.selectbox(
            "分析模式",
            options=["sequential", "parallel"],
            format_func=lambda x: "顺序分析（稳定）" if x == "sequential" else "并行分析（快速）",
            help="顺序分析较慢但稳定，并行分析更快但消耗更多资源"
        )

    with col2:
        max_workers = 1
        if analysis_mode == "parallel":
            max_workers = st.number_input(
                "并行线程数",
                min_value=2.0,
                max_value=5.0,
                value=3.0,
                help="同时分析的股票数量"
            )

    st.markdown("---")

    col_confirm, col_cancel = st.columns(2)

    start_analysis = False
    with col_confirm:
        if st.button("🚀 确认开始分析", type="primary", width='content'):
            start_analysis = True

    with col_cancel:
        if st.button("❌ 取消", type="secondary", width='content'):
            for key in ['main_force_batch_trigger_v2', 'main_force_batch_codes']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    if start_analysis:
        from app import analyze_single_stock_for_batch
        import concurrent.futures

        st.markdown("---")
        st.info("⏳ 正在执行批量分析，请稍候...")

        enabled_analysts_config = {
            'technical': True,
            'fundamental': True,
            'fund_flow': True,
            'risk': True,
            'sentiment': False,
            'news': False
        }
        import config
        selected_model = config.DEFAULT_MODEL_NAME
        period = '1y'

        progress_bar = st.progress(0)
        status_text = st.empty()

        results = []
        start_time = time.time()

        if analysis_mode == "sequential":
            for i, code in enumerate(stock_codes):
                status_text.text(f"正在分析 {code} ({i+1}/{len(stock_codes)})")
                progress_bar.progress((i + 1) / len(stock_codes))

                try:
                    result = analyze_single_stock_for_batch(
                        symbol=code,
                        period=period,
                        enabled_analysts_config=enabled_analysts_config,
                        selected_model=selected_model
                    )
                    results.append(result)
                except Exception as e:
                    results.append({"symbol": code, "success": False, "error": str(e)})

        else:
            def analyze_one(code):
                try:
                    result = analyze_single_stock_for_batch(
                        symbol=code,
                        period=period,
                        enabled_analysts_config=enabled_analysts_config,
                        selected_model=selected_model
                    )
                    return result
                except Exception as e:
                    return {"symbol": code, "success": False, "error": str(e)}

            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(analyze_one, code): code for code in stock_codes}

                completed = 0
                for future in concurrent.futures.as_completed(futures):
                    code = futures[future]
                    completed += 1
                    progress_bar.progress(completed / len(stock_codes))
                    status_text.text(f"已完成 {completed}/{len(stock_codes)} ({code})")

                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        results.append({"symbol": code, "success": False, "error": str(e)})

        progress_bar.empty()
        status_text.empty()

        elapsed_time = time.time() - start_time
        success_count = sum(1 for r in results if r.get("success", False))
        failed_count = len(results) - success_count

        if success_count > 0:
            st.success(f"✅ 批量分析完成！成功 {success_count} 只，失败 {failed_count} 只，耗时 {elapsed_time/60:.1f} 分钟")
        else:
            st.error(f"❌ 所有 {failed_count} 只股票都分析失败！")

            with st.expander("❌ 查看失败原因", expanded=True):
                for r in results:
                    if not r.get("success", False):
                        st.error(f"**{r.get('symbol', 'N/A')}**: {r.get('error', '未知错误')}")

        # 保存结果
        st.session_state.main_force_batch_results = {
            "results": results,
            "total": len(results),
            "success": success_count,
            "failed": failed_count,
            "elapsed_time": elapsed_time,
            "analysis_mode": analysis_mode
        }

        time.sleep(0.5)
        st.rerun()


def display_main_force_batch_results_v2(batch_results):
    """显示V2批量分析结果"""
    results = batch_results['results']
    total = batch_results['total']
    success = batch_results['success']
    failed = batch_results['failed']
    elapsed_time = batch_results['elapsed_time']

    st.markdown("## 📊 V2批量分析结果")

    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("总计分析", f"{total} 只")

    with col2:
        st.metric("成功分析", f"{success} 只", delta=f"{success/total*100:.1f}%")

    with col3:
        st.metric("失败分析", f"{failed} 只")

    with col4:
        st.metric("总耗时", f"{elapsed_time/60:.1f} 分钟")

    st.markdown("---")

    successful_results = [r for r in results if r['success']]

    if successful_results:
        st.markdown(f"### ✅ 成功分析的股票 ({len(successful_results)}只)")

        display_data = []
        for result in successful_results:
            stock_info = result.get('stock_info', {})
            final_decision = result.get('final_decision', {})

            rating = final_decision.get('rating', '未知')
            rating_emoji = {
                '强烈买入': '🔥',
                '买入': '✅',
                '持有': '⏸️',
                '卖出': '⚠️',
                '强烈卖出': '🚫'
            }.get(rating, '❓')

            display_data.append({
                '股票代码': stock_info.get('symbol', ''),
                '股票名称': stock_info.get('name', ''),
                '评级': f"{rating_emoji} {rating}",
                '信心度': final_decision.get('confidence_level', 'N/A'),
                '进场区间': final_decision.get('entry_range', 'N/A'),
                '止盈位': final_decision.get('take_profit', 'N/A'),
                '止损位': final_decision.get('stop_loss', 'N/A'),
                '目标价': final_decision.get('target_price', 'N/A')
            })

        df_display = pd.DataFrame(display_data)

        numeric_cols = ['信心度', '止盈位', '止损位', '目标价']
        for col in numeric_cols:
            if col in df_display.columns:
                df_display[col] = pd.to_numeric(df_display[col], errors='coerce')

        text_cols = ['股票代码', '股票名称', '评级', '进场区间']
        for col in text_cols:
            if col in df_display.columns:
                df_display[col] = df_display[col].astype(str)

        st.dataframe(df_display, width='content', height=400)

        st.markdown("---")
        st.markdown("### 📋 详细分析报告")

        for result in successful_results:
            stock_info = result.get('stock_info', {})
            final_decision = result.get('final_decision', {})

            symbol = stock_info.get('symbol', '')
            name = stock_info.get('name', '')
            rating = final_decision.get('rating', '未知')
            rating_emoji = {
                '强烈买入': '🔥',
                '买入': '✅',
                '持有': '⏸️',
                '卖出': '⚠️',
                '强烈卖出': '🚫'
            }.get(rating, '❓')

            with st.expander(f"{rating_emoji} {symbol} - {name} | {rating}"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("信心度", final_decision.get('confidence_level', 'N/A'))

                with col2:
                    st.metric("进场区间", final_decision.get('entry_range', 'N/A'))

                with col3:
                    st.metric("目标价", final_decision.get('target_price', 'N/A'))

                col1, col2 = st.columns(2)

                with col1:
                    st.metric("止盈位", final_decision.get('take_profit', 'N/A'))

                with col2:
                    st.metric("止损位", final_decision.get('stop_loss', 'N/A'))

                st.markdown("#### 💡 投资建议")
                advice = final_decision.get('operation_advice', final_decision.get('advice', '暂无建议'))
                st.info(advice)

                # 加入监测按钮
                if st.button(f"➕ 加入监测列表", key=f"monitor_v2_{symbol}"):
                    from monitor_db import monitor_db

                    entry_range = final_decision.get('entry_range', '')
                    entry_min, entry_max = None, None
                    if entry_range and isinstance(entry_range, str) and "-" in entry_range:
                        try:
                            parts = entry_range.split("-")
                            entry_min = float(parts[0].strip())
                            entry_max = float(parts[1].strip())
                        except:
                            pass

                    take_profit_str = final_decision.get('take_profit', '')
                    take_profit = None
                    if take_profit_str:
                        try:
                            numbers = re.findall(r'\d+\.?\d*', str(take_profit_str))
                            if numbers:
                                take_profit = float(numbers[0])
                        except:
                            pass

                    stop_loss_str = final_decision.get('stop_loss', '')
                    stop_loss = None
                    if stop_loss_str:
                        try:
                            numbers = re.findall(r'\d+\.?\d*', str(stop_loss_str))
                            if numbers:
                                stop_loss = float(numbers[0])
                        except:
                            pass

                    try:
                        entry_range_dict = {}
                        if entry_min and entry_max:
                            entry_range_dict = {"min": entry_min, "max": entry_max}

                        monitor_db.add_monitored_stock(
                            symbol=symbol,
                            name=name,
                            rating=rating,
                            entry_range=entry_range_dict if entry_range_dict else None,
                            take_profit=take_profit,
                            stop_loss=stop_loss
                        )
                        st.success(f"✅ {symbol} - {name} 已加入监测列表")
                    except Exception as e:
                        st.error(f"❌ 添加失败: {str(e)}")

    failed_results = [r for r in results if not r['success']]

    if failed_results:
        st.markdown("---")
        st.markdown(f"### ❌ 分析失败的股票 ({len(failed_results)}只)")

        failed_data = []
        for result in failed_results:
            failed_data.append({
                '股票代码': result.get('symbol', ''),
                '失败原因': result.get('error', '未知错误')
            })

        df_failed = pd.DataFrame(failed_data)
        st.dataframe(df_failed, width='content')