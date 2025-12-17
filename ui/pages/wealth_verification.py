#!/usr/bin/env python3
"""
财富验证测试页面 (View Layer)
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
    """渲染财富验证页面 (View Layer)"""
    st.set_page_config(page_title="财富验证测试", page_icon="💰", layout="wide")
    
    st.title("💰 财富验证测试中心")
    st.markdown("---")
    
    # MVC: 初始化Controller
    controller = WealthVerificationController()
    
    # [V10.1] 侧边栏：概率分布选项
    with st.sidebar:
        st.header("⚙️ 验证设置")
        use_probabilistic = st.checkbox(
            "📈 启用概率分布验证",
            value=st.session_state.get('use_probabilistic_energy', False),
            help="启用后，验证将基于概率分布（置信区间、Z-score等）而非单一预测值"
        )
        st.session_state['use_probabilistic_energy'] = use_probabilistic
        
        # 设置Controller的概率分布模式
        controller.set_probabilistic_mode(use_probabilistic)
        
        st.markdown("---")
    
    # 侧边栏：导入功能
    with st.sidebar:
        st.header("📥 导入案例")
        uploaded_file = st.file_uploader(
            "上传JSON格式的案例文件",
            type=['json'],
            help="JSON格式：包含 id, name, bazi, day_master, gender, timeline 等字段"
        )
        
        if uploaded_file is not None:
            if st.button("导入案例"):
                try:
                    content = uploaded_file.read()
                    json_data = json.loads(content.decode('utf-8'))
                    
                    # 确保是列表格式
                    if isinstance(json_data, dict):
                        json_data = [json_data]
                    
                    # MVC: 通过Controller导入
                    success, message = controller.import_cases(json_data)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                except Exception as e:
                    st.error(f"导入失败: {str(e)}")
        
        st.markdown("---")
        st.markdown("### 📋 案例格式示例")
        
        example_json = {
            "id": "CASE_001",
            "name": "案例名称",
            "bazi": ["戊午", "癸亥", "壬戌", "丁未"],
            "day_master": "壬",
            "gender": "男",
            "description": "案例描述（可选）",
            "wealth_vaults": ["戌"],
            "timeline": [
                {
                    "year": 2010,
                    "ganzhi": "庚寅",
                    "dayun": "甲子",
                    "type": "WEALTH",
                    "real_magnitude": 100.0,
                    "desc": "财富爆发事件描述"
                },
                {
                    "year": 2012,
                    "ganzhi": "壬辰",
                    "dayun": "甲子",
                    "type": "WEALTH",
                    "real_magnitude": -80.0,
                    "desc": "重大危机事件描述"
                }
            ]
        }
        
        st.json(example_json)
        
        st.markdown("**字段说明：**")
        st.markdown("""
        - `id`: 案例唯一标识
        - `name`: 案例名称
        - `bazi`: 八字四柱（年、月、日、时）
        - `day_master`: 日主天干
        - `gender`: 性别（"男" 或 "女"）
        - `timeline`: 事件时间轴
          - `year`: 年份
          - `ganzhi`: 流年干支
          - `dayun`: 大运干支
          - `real_magnitude`: 真实财富值（-100 到 100）
          - `desc`: 事件描述
        """)
        
        # 下载模板按钮
        st.download_button(
            "📥 下载模板文件",
            data=json.dumps([example_json], ensure_ascii=False, indent=2),
            file_name="wealth_case_template.json",
            mime="application/json"
        )
    
    # MVC: 通过Controller加载案例
    cases = controller.get_all_cases()
    
    if not cases:
        st.warning("⚠️ 未找到案例数据。请先导入案例或运行数据生成脚本。")
        st.info("💡 提示：可以运行 `python3 scripts/create_jason_timeline.py` 创建示例数据")
        return
    
    # 案例选择器
    case_names = [f"{c.name} ({' '.join(c.bazi)})" for c in cases]
    selected_index = st.selectbox("选择案例", range(len(cases)), format_func=lambda i: case_names[i])
    selected_case = cases[selected_index]
    
    st.markdown("---")
    
    # 案例信息
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("案例名称", selected_case.name)
    with col2:
        st.metric("八字", ' '.join(selected_case.bazi))
    with col3:
        st.metric("日主", selected_case.day_master)
    
    # 验证按钮
    if st.button("🚀 开始验证", type="primary"):
        with st.spinner("正在验证..."):
            # MVC: 通过Controller验证
            results = controller.verify_case(selected_case)
            st.session_state[f'results_{selected_case.id}'] = results
            
            # 显示验证完成提示
            if results:
                stats = controller.get_verification_statistics(results)
                st.success(f"✅ 验证完成！共验证 {stats['total_count']} 个事件，命中率 {stats['hit_rate']:.1f}%")
            else:
                st.warning("⚠️ 验证完成，但未获得结果")
    
    # 显示结果
    results_key = f'results_{selected_case.id}'
    if results_key in st.session_state:
        results = st.session_state[results_key]
        
        if not results:
            st.warning("⚠️ 验证结果为空，请重新验证")
            return
        
        # MVC: 通过Controller获取统计信息
        stats = controller.get_verification_statistics(results)
        
        # 统计信息
        st.markdown("### 📊 验证统计")
        
        # [V10.1] 如果启用概率分布，显示额外的统计信息
        if stats.get('probabilistic_mode', False):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("命中率", f"{stats['correct_count']}/{stats['total_count']} ({stats['hit_rate']:.1f}%)")
            with col2:
                st.metric("置信区间命中率", f"{stats['confidence_interval_hit_rate']:.1f}%",
                         help="真实值在预测置信区间（25%-75%）内的比例")
            with col3:
                st.metric("平均Z-score", f"{stats['avg_z_score']:.2f}",
                         help="真实值距离预测均值的标准差倍数，绝对值越小越好")
            with col4:
                st.metric("验证状态", stats['status'])
            
            st.markdown("---")
            st.info(f"📊 **概率分布模式**：使用置信区间和Z-score进行验证。置信区间命中率：{stats['confidence_interval_hit_rate']:.1f}%")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("命中率", f"{stats['correct_count']}/{stats['total_count']} ({stats['hit_rate']:.1f}%)")
            with col2:
                st.metric("平均误差", f"{stats['avg_error']:.1f}分")
            with col3:
                st.metric("验证状态", stats['status'])
        
        st.markdown("---")
        
        # 结果表格
        st.subheader("📊 测试结果详情")
        
        table_data = []
        for r in results:
            if r.get('error') is not None:
                # [V10.1] 如果启用概率分布，显示更多信息
                if r.get('wealth_distribution'):
                    predicted_display = f"{r.get('predicted_mean', r.get('predicted', 0)):.1f} ± {r.get('predicted_std', 0):.1f}"
                    table_data.append({
                        '年份': r['year'],
                        '流年': r['ganzhi'],
                        '大运': r['dayun'],
                        '真实值': r['real'],
                        '预测值（均值±标准差）': predicted_display,
                        '置信区间': f"[{r.get('predicted_p25', 0):.1f}, {r.get('predicted_p75', 0):.1f}]",
                        'Z-score': f"{r.get('z_score', 0):.2f}",
                        '误差': f"{r['error']:.1f}",
                        '状态': '✅' if r['is_correct'] else '❌',
                        '财库': '🏆' if r.get('vault_opened') else ('💀' if r.get('vault_collapsed') else '🔒'),
                        '强根': '✅' if r.get('strong_root') else '❌'
                    })
                else:
                    table_data.append({
                        '年份': r['year'],
                        '流年': r['ganzhi'],
                        '大运': r['dayun'],
                        '真实值': r['real'],
                        '预测值': r.get('predicted', 'N/A') if r.get('predicted') is not None else 'N/A',
                        '误差': f"{r['error']:.1f}",
                        '状态': '✅' if r['is_correct'] else '❌',
                        '财库': '🏆' if r.get('vault_opened') else ('💀' if r.get('vault_collapsed') else '🔒'),
                        '强根': '✅' if r.get('strong_root') else '❌'
                    })
            else:
                table_data.append({
                    '年份': r['year'],
                    '流年': r['ganzhi'],
                    '大运': r['dayun'],
                    '真实值': r['real'],
                    '预测值': '计算失败',
                    '误差': '-',
                    '状态': '❌',
                    '财库': '-',
                    '强根': '-'
                })
        
        if table_data:
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True)
            
            # 添加文本摘要
            st.markdown("#### 📝 结果摘要")
            correct_count = sum(1 for r in results if r.get('is_correct', False))
            total_count = len(results)
            
            st.write(f"**验证完成**：共验证 {total_count} 个事件，其中 {correct_count} 个预测正确（误差 ≤ 20分）")
            
            # 列出每个事件的结果
            st.write("**详细结果**：")
            for r in results:
                status_icon = "✅" if r.get('is_correct', False) else "❌"
                real = r.get('real', 0.0)
                predicted = r.get('predicted', 'N/A')
                error = r.get('error', 'N/A')
                
                if predicted != 'N/A' and error != 'N/A':
                    st.write(f"- {status_icon} **{r['year']}年** ({r['ganzhi']}): 真实值={real:.1f}, 预测值={predicted:.1f}, 误差={error:.1f}分")
                else:
                    st.write(f"- {status_icon} **{r['year']}年** ({r['ganzhi']}): 真实值={real:.1f}, 预测值=计算失败")
        else:
            st.warning("⚠️ 没有可显示的结果数据")
        
        # 折线图
        st.markdown("---")
        st.subheader("📈 财富预测折线图")
        
        years = [r['year'] for r in results]
        real_values = [r['real'] for r in results]
        predicted_values = [r.get('predicted', 0) if r.get('predicted') is not None else 0 for r in results]
        
        # [V10.1] 检查是否启用概率分布
        use_probabilistic = st.session_state.get('use_probabilistic_energy', False)
        has_distributions = any(r.get('wealth_distribution') for r in results)
        
        fig = go.Figure()
        
        # [V10.1] 如果启用概率分布，显示置信区间
        if use_probabilistic and has_distributions:
            # 提取置信区间数据
            dist_years = [r['year'] for r in results if r.get('wealth_distribution')]
            dist_means = [r.get('predicted_mean', r.get('predicted', 0)) for r in results if r.get('wealth_distribution')]
            dist_lowers = [r.get('predicted_p25', 0) for r in results if r.get('wealth_distribution')]
            dist_uppers = [r.get('predicted_p75', 0) for r in results if r.get('wealth_distribution')]
            
            # 1. 添加置信区间（阴影区域）
            fig.add_trace(go.Scatter(
                x=dist_years + dist_years[::-1],
                y=dist_uppers + dist_lowers[::-1],
                fill='toself',
                fillcolor='rgba(255, 215, 0, 0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                hoverinfo="skip",
                showlegend=True,
                name='预测置信区间 (25%-75%)'
            ))
            
            # 2. 添加预测均值折线
            fig.add_trace(go.Scatter(
                x=dist_years,
                y=dist_means,
                mode='lines+markers',
                name='AI预测值 (均值)',
                line=dict(color='#FFD700', width=3, dash='dash', shape='spline'),
                marker=dict(size=8, color='#FFD700'),
                hovertemplate='%{x}年: 预测均值 %{y:.1f}<extra></extra>'
            ))
        else:
            # 传统模式：单一预测值
            fig.add_trace(go.Scatter(
                x=years,
                y=predicted_values,
                mode='lines+markers',
                name='AI预测值',
                line=dict(color='#FFD700', width=3, dash='dash', shape='spline'),
                marker=dict(size=8, color='#FFD700'),
                hovertemplate='%{x}年: 预测值 %{y:.1f}<extra></extra>'
            ))
        
        # 真实值折线（始终显示）
        fig.add_trace(go.Scatter(
            x=years,
            y=real_values,
            mode='lines+markers',
            name='真实值 (Ground Truth)',
            line=dict(color='#00E5FF', width=3, shape='spline'),
            marker=dict(size=8, color='#00E5FF'),
            hovertemplate='%{x}年: 真实值 %{y:.1f}<extra></extra>'
        ))
        
        # 标注关键事件
        for r in results:
            if r.get('vault_opened'):
                fig.add_annotation(
                    x=r['year'],
                    y=max(r.get('predicted', 0), r['real']) + 10,
                    text="🏆",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor="#FFD700",
                    font=dict(size=20)
                )
            elif r.get('vault_collapsed'):
                fig.add_annotation(
                    x=r['year'],
                    y=min(r.get('predicted', 0), r['real']) - 10,
                    text="💀",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor="#FF0000",
                    font=dict(size=20)
                )
        
        fig.update_layout(
            title="财富预测对比 (真实值 vs AI预测)",
            xaxis_title="年份",
            yaxis_title="财富指数",
            yaxis=dict(range=[-100, 100]),
            height=500,
            hovermode="x unified",
            plot_bgcolor='rgba(0,0,0,0.05)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # [V9.3 MCP] 事件锚点用户输入功能
        st.markdown("---")
        st.subheader("📝 添加实际事件 (MCP: 交互上下文)")
        st.caption("💡 点击图表上的年份，或手动输入实际发生的财富事件，用于模型校准")
        
        input_col1, input_col2 = st.columns(2)
        with input_col1:
            input_year = st.number_input("年份", min_value=1900, max_value=2100, value=2024, step=1)
            input_ganzhi = st.text_input("流年干支", value="", placeholder="如：甲子", help="可选，如果不填将自动计算")
            input_dayun = st.text_input("大运干支", value="", placeholder="如：乙丑", help="可选")
        
        with input_col2:
            input_real_value = st.number_input("实际财富值", min_value=-100.0, max_value=100.0, value=0.0, step=1.0, 
                                             help="真实发生的财富变化值（-100 到 100）")
            input_desc = st.text_area("事件描述", value="", placeholder="描述该年发生的财富事件", height=100)
        
        if st.button("💾 保存事件", type="primary"):
            if input_desc:
                try:
                    # 通过 Controller 保存用户反馈
                    success, message = controller.add_user_feedback(
                        case_id=selected_case.id,
                        year=input_year,
                        ganzhi=input_ganzhi if input_ganzhi else None,
                        dayun=input_dayun if input_dayun else None,
                        real_magnitude=input_real_value,
                        description=input_desc
                    )
                    if success:
                        st.success(f"✅ {message}")
                        st.info("💡 事件已保存，将用于模型校准。请重新验证以查看更新后的结果。")
                        # 清除结果缓存，强制重新验证
                        if results_key in st.session_state:
                            del st.session_state[results_key]
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                except Exception as e:
                    st.error(f"保存失败: {str(e)}")
            else:
                st.warning("⚠️ 请填写事件描述")
        
        # 详细分析流程
        st.markdown("---")
        st.subheader("🔍 详细分析流程")
        
        for i, r in enumerate(results, 1):
            with st.expander(f"{r['year']}年 ({r['ganzhi']}) - {r.get('desc', '')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**基本信息**")
                    st.write(f"- 流年: {r['ganzhi']}")
                    st.write(f"- 大运: {r['dayun']}")
                    st.write(f"- 真实值: {r['real']:.1f}")
                    if r.get('predicted') is not None:
                        st.write(f"- 预测值: {r['predicted']:.1f}")
                        st.write(f"- 误差: {r['error']:.1f}")
                    else:
                        st.write(f"- 预测值: 计算失败")
                        st.write(f"- 错误: {r.get('error_msg', 'Unknown')}")
                
                with col2:
                    st.markdown("**关键指标**")
                    if r.get('strength_score') is not None:
                        st.write(f"- 身强分数: {r['strength_score']:.1f} ({r.get('strength_label', 'Unknown')})")
                    if r.get('opportunity') is not None:
                        st.write(f"- 机会能量: {r['opportunity']:.1f}")
                    st.write(f"- 财库状态: {'🏆 已冲开' if r.get('vault_opened') else ('💀 已坍塌' if r.get('vault_collapsed') else '🔒 未变化')}")
                    st.write(f"- 强根: {'✅ 有' if r.get('strong_root') else '❌ 无'}")
                
                if r.get('details'):
                    st.markdown("**触发机制**")
                    for detail in r['details']:
                        st.write(f"- {detail}")
                
                if not r.get('is_correct', True) and r.get('error') is not None:
                    st.markdown("**问题分析**")
                    error = r['error']
                    if error > 30:
                        st.warning(f"⚠️ 预测偏差较大 ({error:.1f}分)，可能原因：")
                        st.write("1. 身强身弱判断不准确")
                        st.write("2. 财库冲开/坍塌逻辑需要调优")
                        st.write("3. 其他特殊格局未识别")
                    elif error > 20:
                        st.info(f"ℹ️ 预测偏差中等 ({error:.1f}分)，建议检查：")
                        st.write("1. 参数权重是否需要微调")
                        st.write("2. 事件触发条件是否准确")

if __name__ == "__main__":
    render()

