#!/usr/bin/env python3
"""
V12.0 量子财富引力场验证页面 (View Layer)
MVC View - 只负责UI展示，所有业务逻辑通过Controller处理
"""

import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# MVC: 只导入Controller，不直接操作Model或Engine
from controllers.wealth_verification_controller import WealthVerificationController


def render():
    """渲染V12.0量子财富场页面 (View Layer)"""
    st.set_page_config(
        page_title="V12.0 量子财富引力场", 
        page_icon="🌊", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 页面标题
    st.title("🌊 V12.0 量子财富引力场")
    st.caption("基于F, C, σ三维向量模型的0-100岁完整时间序列模拟与验证")
    st.markdown("---")
    
    # MVC: 初始化Controller
    controller = WealthVerificationController()
    
    # 加载名人案例库
    celeb_file = Path(project_root) / "data" / "celebrity_wealth.json"
    celebrities = []
    
    if celeb_file.exists():
        try:
            with open(celeb_file, 'r', encoding='utf-8') as f:
                celebrities = json.load(f)
        except Exception as e:
            st.error(f"❌ 加载名人案例库失败: {e}")
    else:
        st.warning("⚠️ 名人案例库文件不存在，请先创建 `data/celebrity_wealth.json`")
    
    if not celebrities:
        st.info("💡 提示：名人案例库为空，请先添加案例数据")
        return
    
    # ========== 侧边栏：案例选择与信息 ==========
    with st.sidebar:
        st.header("🎯 案例选择")
        
        # 选择名人
        celeb_names = [f"{c['name']} ({c.get('birth_year', '?')}年)" for c in celebrities]
        selected_celeb_idx = st.selectbox(
            "选择名人案例",
            range(len(celebrities)),
            format_func=lambda i: celeb_names[i],
            help="从名人案例库中选择要验证的案例"
        )
        selected_celeb = celebrities[selected_celeb_idx]
        
        st.markdown("---")
        
        # 案例信息卡片
        st.header("📋 案例信息")
        st.markdown(f"**姓名**: {selected_celeb['name']}")
        st.markdown(f"**八字**: {' '.join(selected_celeb['bazi'])}")
        st.markdown(f"**日主**: {selected_celeb['day_master']}")
        st.markdown(f"**性别**: {selected_celeb['gender']}")
        st.markdown(f"**出生年**: {selected_celeb.get('birth_year', '?')}")
        st.markdown(f"**描述**: {selected_celeb.get('description', '无')}")
        
        st.markdown("---")
        
        # 事件统计
        events = selected_celeb.get('events', [])
        if events:
            st.header("📊 事件统计")
            boom_count = sum(1 for e in events if e.get('type') == 'boom')
            crash_count = sum(1 for e in events if e.get('type') == 'crash')
            spike_count = sum(1 for e in events if e.get('type') == 'spike')
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("总事件数", len(events))
                st.metric("🏆 发财", boom_count)
            with col2:
                st.metric("💀 破财", crash_count)
                st.metric("📌 其他", spike_count)
    
    # ========== 主界面：模拟控制 ==========
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader("🚀 模拟控制")
    
    with col2:
        lifespan = st.number_input(
            "模拟年限",
            min_value=50,
            max_value=120,
            value=100,
            step=10,
            help="模拟从出生到指定年龄的财富曲线"
        )
    
    with col3:
        if st.button("🚀 开始模拟", type="primary", use_container_width=True):
            with st.spinner(f"正在模拟0-{lifespan}岁完整人生财富曲线..."):
                try:
                    from core.wealth_engine import simulate_life_wealth
                    
                    # 执行模拟
                    timeline = simulate_life_wealth(
                        bazi=selected_celeb['bazi'],
                        day_master=selected_celeb['day_master'],
                        gender=selected_celeb['gender'],
                        birth_year=selected_celeb['birth_year'],
                        lifespan=lifespan
                    )
                    
                    st.session_state[f'v12_timeline_{selected_celeb["id"]}'] = timeline
                    st.session_state[f'v12_lifespan_{selected_celeb["id"]}'] = lifespan
                    st.success(f"✅ 模拟完成！共生成 {len(timeline)} 个数据点（0-{lifespan}岁）")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ 模拟失败: {str(e)}")
                    import traceback
                    with st.expander("查看错误详情"):
                        st.code(traceback.format_exc())
    
    st.markdown("---")
    
    # ========== 显示结果 ==========
    timeline_key = f'v12_timeline_{selected_celeb["id"]}'
    if timeline_key not in st.session_state:
        st.info("💡 请点击「开始模拟」按钮生成财富曲线")
        return
    
    timeline = st.session_state[timeline_key]
    saved_lifespan = st.session_state.get(f'v12_lifespan_{selected_celeb["id"]}', 100)
    
    if not timeline:
        st.warning("⚠️ 模拟结果为空，请重新模拟")
        return
    
    # 提取Ground Truth事件
    gt_events = selected_celeb.get('events', [])
    
    # ========== 财富曲线可视化 ==========
    st.subheader("📈 0-100岁财富曲线")
    
    years = [item['year'] for item in timeline]
    scores = [item['score'] for item in timeline]
    
    fig = go.Figure()
    
    # 1. 添加模拟曲线（蓝色）
    fig.add_trace(go.Scatter(
        x=years,
        y=scores,
        mode='lines',
        name='V12.0 模拟曲线',
        line=dict(color='#3B82F6', width=3, shape='spline'),
        hovertemplate='%{x}年 (年龄%{customdata}岁): 财富势能 %{y:.1f}<extra></extra>',
        customdata=[item['age'] for item in timeline]
    ))
    
    # 2. 添加Ground Truth真实值折线（如果事件足够多）
    if len(gt_events) >= 3:
        gt_years = [event['year'] for event in gt_events]
        gt_magnitudes = [event.get('magnitude', 0.0) for event in gt_events]
        
        fig.add_trace(go.Scatter(
            x=gt_years,
            y=gt_magnitudes,
            mode='lines+markers',
            name='真实值 (Ground Truth)',
            line=dict(color='#EF4444', width=2, dash='dot', shape='spline'),
            marker=dict(size=8, color='#EF4444'),
            hovertemplate='%{x}年: 真实值 %{y:.1f}<extra></extra>'
        ))
    
    # 3. 叠加Ground Truth事件标记
    boom_years = []
    boom_magnitudes = []
    crash_years = []
    crash_magnitudes = []
    spike_years = []
    spike_magnitudes = []
    event_descriptions = {}
    
    for event in gt_events:
        year = event['year']
        magnitude = event.get('magnitude', 0.0)
        event_type = event.get('type', 'spike')
        desc = event.get('desc', '')
        
        # 找到对应年份的模拟值
        sim_item = next((item for item in timeline if item['year'] == year), None)
        sim_value = sim_item['score'] if sim_item else None
        error = abs(sim_value - magnitude) if sim_value is not None else None
        
        event_descriptions[year] = {
            'desc': desc,
            'magnitude': magnitude,
            'sim_value': sim_value,
            'error': error
        }
        
        if event_type == 'boom':
            boom_years.append(year)
            boom_magnitudes.append(magnitude)
        elif event_type == 'crash':
            crash_years.append(year)
            crash_magnitudes.append(magnitude)
        else:
            spike_years.append(year)
            spike_magnitudes.append(magnitude)
    
    # 发财年标记
    if boom_years:
        hover_texts = []
        for year in boom_years:
            sim_val = event_descriptions[year]['sim_value']
            error_val = event_descriptions[year]['error']
            sim_val_str = f"{sim_val:.1f}" if sim_val is not None else "N/A"
            error_val_str = f"{error_val:.1f}" if error_val is not None else "N/A"
            hover_text = (
                f"{year}年: {event_descriptions[year]['desc']}<br>"
                f"真实值: {event_descriptions[year]['magnitude']:.1f}<br>"
                f"模拟值: {sim_val_str}<br>"
                f"误差: {error_val_str}"
            )
            hover_texts.append(hover_text)
        
        fig.add_trace(go.Scatter(
            x=boom_years,
            y=boom_magnitudes,
            mode='markers+text',
            name='🏆 真实事件: 发财',
            marker=dict(symbol='triangle-up', size=18, color='#EF4444', line=dict(width=2, color='white')),
            text=[f"{year}" for year in boom_years],
            textposition="top center",
            textfont=dict(size=10, color='#EF4444'),
            hovertemplate='%{hovertext}<extra></extra>',
            hovertext=hover_texts
        ))
    
    # 破财年标记
    if crash_years:
        hover_texts = []
        for year in crash_years:
            sim_val = event_descriptions[year]['sim_value']
            error_val = event_descriptions[year]['error']
            sim_val_str = f"{sim_val:.1f}" if sim_val is not None else "N/A"
            error_val_str = f"{error_val:.1f}" if error_val is not None else "N/A"
            hover_text = (
                f"{year}年: {event_descriptions[year]['desc']}<br>"
                f"真实值: {event_descriptions[year]['magnitude']:.1f}<br>"
                f"模拟值: {sim_val_str}<br>"
                f"误差: {error_val_str}"
            )
            hover_texts.append(hover_text)
        
        fig.add_trace(go.Scatter(
            x=crash_years,
            y=crash_magnitudes,
            mode='markers+text',
            name='💀 真实事件: 破财',
            marker=dict(symbol='triangle-down', size=18, color='#10B981', line=dict(width=2, color='white')),
            text=[f"{year}" for year in crash_years],
            textposition="bottom center",
            textfont=dict(size=10, color='#10B981'),
            hovertemplate='%{hovertext}<extra></extra>',
            hovertext=hover_texts
        ))
    
    # 一般事件标记
    if spike_years:
        hover_texts = []
        for year in spike_years:
            sim_val = event_descriptions[year]['sim_value']
            error_val = event_descriptions[year]['error']
            sim_val_str = f"{sim_val:.1f}" if sim_val is not None else "N/A"
            error_val_str = f"{error_val:.1f}" if error_val is not None else "N/A"
            hover_text = (
                f"{year}年: {event_descriptions[year]['desc']}<br>"
                f"真实值: {event_descriptions[year]['magnitude']:.1f}<br>"
                f"模拟值: {sim_val_str}<br>"
                f"误差: {error_val_str}"
            )
            hover_texts.append(hover_text)
        
        fig.add_trace(go.Scatter(
            x=spike_years,
            y=spike_magnitudes,
            mode='markers+text',
            name='📌 真实事件: 其他',
            marker=dict(symbol='circle', size=12, color='#F59E0B', line=dict(width=2, color='white')),
            text=[f"{year}" for year in spike_years],
            textposition="top center",
            textfont=dict(size=9, color='#F59E0B'),
            hovertemplate='%{hovertext}<extra></extra>',
            hovertext=hover_texts
        ))
    
    fig.update_layout(
        title=f"{selected_celeb['name']} - 0-{saved_lifespan}岁财富曲线 (V12.0 量子财富场)",
        xaxis_title="年份",
        yaxis_title="财富势能 (W = F × C × (1 + σ))",
        height=600,
        hovermode="x unified",
        plot_bgcolor='rgba(0,0,0,0.05)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ========== 拟合度分析 ==========
    st.markdown("---")
    st.subheader("📊 拟合度分析")
    
    if gt_events:
        # 计算所有事件的误差
        errors = []
        boom_hits = 0
        boom_total = 0
        crash_hits = 0
        crash_total = 0
        
        for event in gt_events:
            year = event['year']
            magnitude = event.get('magnitude', 0.0)
            event_type = event.get('type', 'spike')
            
            sim_item = next((item for item in timeline if item['year'] == year), None)
            if sim_item:
                sim_value = sim_item['score']
                error = abs(sim_value - magnitude)
                errors.append(error)
                
                if error <= 20.0:
                    if event_type == 'boom':
                        boom_hits += 1
                    elif event_type == 'crash':
                        crash_hits += 1
            
            if event_type == 'boom':
                boom_total += 1
            elif event_type == 'crash':
                crash_total += 1
        
        avg_error = sum(errors) / len(errors) if errors else 0.0
        max_error = max(errors) if errors else 0.0
        min_error = min(errors) if errors else 0.0
        
        # 计算Top 20%阈值
        sorted_scores = sorted(scores, reverse=True)
        top_20_threshold = sorted_scores[int(len(sorted_scores) * 0.2)] if len(sorted_scores) > 0 else 0
        
        boom_top20_hits = 0
        for event in gt_events:
            if event.get('type') == 'boom':
                year = event['year']
                sim_value = next((item['score'] for item in timeline if item['year'] == year), None)
                if sim_value and sim_value >= top_20_threshold:
                    boom_top20_hits += 1
        
        boom_top20_rate = (boom_top20_hits / boom_total * 100) if boom_total > 0 else 0.0
        overall_hit_rate = ((boom_hits + crash_hits) / (boom_total + crash_total) * 100) if (boom_total + crash_total) > 0 else 0.0
        
        # 显示统计信息
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总体拟合度", f"{overall_hit_rate:.1f}%", 
                     f"{boom_hits + crash_hits}/{boom_total + crash_total} 事件命中")
        with col2:
            st.metric("发财年Top20%", f"{boom_top20_rate:.1f}%", 
                     f"{boom_top20_hits}/{boom_total} 在曲线高点")
        with col3:
            st.metric("平均误差", f"{avg_error:.1f}分", 
                     f"范围: {min_error:.1f} - {max_error:.1f}")
        with col4:
            st.metric("曲线峰值", f"{max(scores):.1f}", 
                     f"Top 20%阈值: {top_20_threshold:.1f}")
        
        # 详细事件对比表
        st.markdown("---")
        st.subheader("📋 事件对比详情")
        
        comparison_data = []
        for event in gt_events:
            year = event['year']
            magnitude = event.get('magnitude', 0.0)
            event_type = event.get('type', 'spike')
            desc = event.get('desc', '')
            
            sim_item = next((item for item in timeline if item['year'] == year), None)
            if sim_item:
                sim_value = sim_item['score']
                error = abs(sim_value - magnitude)
                is_match = error <= 20.0
                
                comparison_data.append({
                    '年份': year,
                    '事件类型': '🏆 发财' if event_type == 'boom' else ('💀 破财' if event_type == 'crash' else '📌 其他'),
                    '事件描述': desc,
                    '真实值': f"{magnitude:.1f}",
                    '模拟值': f"{sim_value:.1f}",
                    '误差': f"{error:.1f}",
                    '状态': '✅ 命中' if is_match else '❌ 未命中'
                })
        
        if comparison_data:
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True)
    else:
        st.info("💡 该案例暂无Ground Truth事件数据")
    
    # ========== 向量调试区 ==========
    st.markdown("---")
    st.subheader("🔍 向量调试区")
    st.caption("选择年份查看F, C, σ向量的详细数值")
    
    selected_year = st.selectbox(
        "选择年份",
        options=[item['year'] for item in timeline],
        format_func=lambda y: f"{y}年 (年龄{next((item['age'] for item in timeline if item['year'] == y), '?')}岁)",
        key=f"debug_year_{selected_celeb['id']}"
    )
    
    selected_data = next((item for item in timeline if item['year'] == selected_year), None)
    if selected_data:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("F (流量)", f"{selected_data['flow_vector']:.3f}",
                     help="能量流向财星的顺畅度")
        with col2:
            st.metric("C (掌控)", f"{selected_data['capacity_vector']:.3f}",
                     help="日主获取并留存能量的能力")
        with col3:
            st.metric("σ (波动)", f"{selected_data['volatility_sigma']:.3f}",
                     help="系统的震荡幅度")
        with col4:
            w = selected_data['flow_vector'] * selected_data['capacity_vector'] * (1 + selected_data['volatility_sigma']) * 100
            st.metric("W (势能)", f"{w:.1f}",
                     help="W = F × C × (1 + σ) × 100")
        
        st.markdown(f"**流年**: {selected_data['year_pillar']} | **大运**: {selected_data['luck_pillar']} | **身强**: {selected_data['strength_type']}")


if __name__ == "__main__":
    render()
