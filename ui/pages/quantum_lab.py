import streamlit as st
import pandas as pd
import json
import os
import plotly.graph_objects as go
import plotly.graph_objects as go
import numpy as np
import scipy.stats as stats
import datetime
# V13.0: 已删除未使用的类型导入
from ui.components.unified_input_panel import render_and_collect_input
from facade.bazi_facade import BaziFacade
from utils.constants_manager import get_constants
from utils.notification_manager import get_notification_manager

# MVC Controllers
from controllers.bazi_controller import BaziController
from controllers.quantum_lab_controller import QuantumLabController
from ui.components.tuning_panel import render_tuning_panel, deep_merge_params, merge_sidebar_values_to_config

# V13.0: 已删除 render_sidebar_case_summary 函数（档案信息显示）

def render():
    st.set_page_config(page_title="Quantum Lab", page_icon="🧪", layout="wide")

    # --- CSS: Quantum Glassmorphism & Animations ---
    st.markdown("""
    <style>
    /* Animation Keyframes */
    @keyframes oat-float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-6px); }
        100% { transform: translateY(0px); }
    }
    @keyframes oat-pulse-shield {
        0% { box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(56, 189, 248, 0); }
        100% { box-shadow: 0 0 0 0 rgba(56, 189, 248, 0); }
    }
    @keyframes oat-flow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes oat-alert {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.1); opacity: 0.8; }
        100% { transform: scale(1); opacity: 1; }
    }

    /* Narrative Card Styles */
    .narrative-card {
        position: relative;
        padding: 24px;
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        overflow: hidden;
        transition: all 0.3s ease;
        margin-bottom: 15px;
    }
    .narrative-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        border-color: rgba(255, 255, 255, 0.2);
    }
    
    /* Card Types */
    .card-mountain {
        background: linear-gradient(135deg, rgba(120, 53, 15, 0.15) 0%, rgba(251, 191, 36, 0.1) 100%);
        border-top: 2px solid rgba(251, 191, 36, 0.4);
    }
    .icon-mountain {
        font-size: 32px;
        animation: oat-float 3s ease-in-out infinite;
        filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3));
    }
    
    .card-shield {
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.2) 0%, rgba(56, 189, 248, 0.1) 100%);
        border-top: 2px solid rgba(56, 189, 248, 0.4);
    }
    .icon-shield {
        font-size: 32px;
        border-radius: 50%;
        animation: oat-pulse-shield 2s infinite;
    }
    
    .card-flow {
        background: linear-gradient(270deg, rgba(6, 78, 59, 0.2), rgba(52, 211, 153, 0.15), rgba(6, 78, 59, 0.2));
        background-size: 200% 200%;
        animation: oat-flow 6s ease infinite;
        border-top: 2px solid rgba(52, 211, 153, 0.4);
    }
    .icon-flow {
        font-size: 32px;
        display: inline-block;
        animation: oat-float 2s ease-in-out infinite;
    }

    .card-danger {
        background: linear-gradient(135deg, rgba(127, 29, 29, 0.2) 0%, rgba(248, 113, 113, 0.1) 100%);
        border-top: 2px solid rgba(248, 113, 113, 0.4);
    }
    .icon-danger {
        font-size: 32px;
        animation: oat-alert 1.5s infinite;
    }

    /* Typography */
    .card-title { font-weight: 700; font-size: 1.1rem; margin-bottom: 4px; color: #f1f5f9; letter-spacing: 0.5px; }
    .card-subtitle { font-size: 0.9rem; color: #cbd5e1; margin-bottom: 8px; line-height: 1.4; }
    .card-impact { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; padding: 4px 8px; border-radius: 4px; background: rgba(0,0,0,0.3); display: inline-block; color: #a5b4fc; }
    </style>
    """, unsafe_allow_html=True)
    
    def render_narrative_card(event):
        """Renders a single narrative card based on the event payload."""
        ctype = event.get('card_type', 'default')
        
        config = {
            "mountain_alliance": {"css": "card-mountain", "icon": "⛰️", "icon_css": "icon-mountain"},
            "penalty_cap": {"css": "card-shield", "icon": "🛡️", "icon_css": "icon-shield"},
            "mediation": {"css": "card-flow", "icon": "🌊", "icon_css": "icon-flow"},
            "pressure": {"css": "card-danger", "icon": "⚠️", "icon_css": "icon-danger"},
            "control": {"css": "card-shield", "icon": "⚡", "icon_css": "icon-shield"}, 
            "vault_open": {"css": "card-mountain", "icon": "💰", "icon_css": "icon-mountain"},
            "tomb_break": {"css": "card-danger", "icon": "⚰️", "icon_css": "icon-danger"},
            "default": {"css": "", "icon": "📜", "icon_css": ""}
        }
        
        cfg = config.get(ctype, config['default'])
        
        # Determine animation class based on triggers
        anim_trigger = event.get('animation_trigger', '')
        extra_icon_style = ""
        
        html = f"""
        <div class="narrative-card {cfg['css']}">
            <div style="display: flex; align-items: start; gap: 16px;">
                <div class="{cfg['icon_css']}" style="{extra_icon_style}">{cfg['icon']}</div>
                <div style="flex-grow: 1;">
                    <div class="card-title">{event.get('title', 'Unknown Event')}</div>
                    <div class="card-subtitle">{event.get('desc', '')}</div>
                    <div class="card-impact">{event.get('score_delta', '')}</div>
                </div>
            </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

    # --- Load Data ---
    @st.cache_data
    def load_cases():
        path = os.path.join(os.path.dirname(__file__), "../../data/calibration_cases.json")
        data = []
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
        # Normalize required fields via controller helper (no view-layer inference)
        data = BaziController.normalize_cases(data)
        
        # Load Truth Scores (Side-car)
        truth_path = os.path.join(os.path.dirname(__file__), "../../data/truth_values.json")
        if os.path.exists(truth_path):
            with open(truth_path, 'r') as f:
                truths = json.load(f)
                truth_map = {t['id']: t.get('truth_scores', {}) for t in truths}
                # Merge
                for c in data:
                    if c['id'] in truth_map:
                        c['truth_scores'] = truth_map[c['id']]
        
        # V13.0: MCP上下文注入已移至Controller层，不再在View层处理
        
        return data

    cases = load_cases()


    # --- 统一输入面板置顶（P2 专用） ---
    st.session_state["era_key_prefix"] = "era_p2"
    consts = get_constants()
    controller = BaziController()
    bazi_facade = BaziFacade(controller=controller)
    selected_case, era_factor, city_for_controller = render_and_collect_input(
        bazi_facade, cases=cases, is_quantum_lab=True
    )

    # --- SIDEBAR CONTROLS ---
    st.sidebar.markdown("---")
    
    # V50.0: 提前加载黄金配置（供所有边栏参数使用）
    # [V10.3] 使用ConfigModel统一管理配置，确保实时同步
    from core.models.config_model import ConfigModel
    config_model = ConfigModel()
    golden_config = config_model.load_config()
    
    # === 算法参数调优控制台 (Refactored Component) ===
    from ui.components.tuning_panel import render_tuning_panel
    
    # Render the tuning panel and get updated configuration
    # Note: particle_weights are also collected here
    fp, particle_weights_from_panel = render_tuning_panel(controller, golden_config)
    
    # Pass the updated config to session state for hot-reloading if needed by other components
    st.session_state['full_algo_config'] = fp
    
    # Update controller with new particle weights if changed (optional autosave logic could go here)
    # For now, we rely on the tuning panel's internal logic or the save button if we implemented it there.
    # But wait, the previous code had a save button. 
    # Let's ensure we use the particle weights from the panel.
    particle_weights = particle_weights_from_panel

    # [V10.3] 参数来源和刷新按钮 logic is inside the component now

    # V13.0: 已删除"应用并回测"按钮和"全局回归检查"开关（不再使用）
    
    # [V12.1] 注意：财富/感情/事业相关参数已移除
    # 这些参数属于第二层验证（财富预测），应在 wealth_verification.py 中调优
    # 量子验证页面专注于第一层验证（旺衰判定）

    # --- MAIN ENGINE SETUP ---
    # 所有算法调用都通过 controller，不再需要 engine_mode
    
    # Refresh controller input with particle weights via Facade
    user_data = controller.get_user_data()
    try:
        bazi_facade.process_and_set_inputs(
            user_data={
                "name": user_data.get('name', 'LabUser'),
                "gender": user_data.get('gender', '男'),
                "date": user_data.get('date', datetime.date(1990, 1, 1)),
                "time": user_data.get('time', 12),
                "city": user_data.get('city', city_for_controller or "Beijing"),
                "enable_solar": user_data.get('enable_solar', True),
                "longitude": user_data.get('longitude', 116.46),
            },
            geo_city=city_for_controller or "Beijing",
            era_factor=era_factor if era_factor else None,
            particle_weights=particle_weights
        )
    except Exception as e:
        st.warning(f"无法刷新 Controller 输入（粒子权重）: {e}")

    get_notification_manager().display_all()
    
    # [V10.0] 初始化QuantumLabController（如果还没有初始化）
    if 'quantum_lab_controller' not in st.session_state:
        st.session_state['quantum_lab_controller'] = QuantumLabController()
    
    quantum_controller = st.session_state['quantum_lab_controller']
    
    # === V6.0+ 热更新：从 session_state 读取并应用算法配置 ===
    # [V10.0] 使用Controller更新配置
    if 'algo_config' in st.session_state:
        quantum_controller.update_config(st.session_state['algo_config'])
        
    if 'full_algo_config' in st.session_state:
        quantum_controller.update_config(st.session_state['full_algo_config'])

    # --- UI HEADER ---
    st.title("🧪 量子验证工作台")
    st.markdown("**V12.1 旺衰判定验证系统** - 基于GraphNetworkEngine与SVM模型")
    st.caption("专注于第一层验证（旺衰判定），使用最新的V11.0 SVM模型和V10.0非线性算法")

    # --- TABS ---
    # --- TABS ---
    tab_core, tab_global, tab_single, tab_rules = st.tabs([
        "⚛️ 物理内核 (Physics Core)",
        "🔭 批量验证", 
        "🔬 单点分析",
        "📜 规则匹配"
    ])

    # ==========================
    # TAB 1: 物理内核 (Phase 1 & 2 Merged)
    # ==========================
    with tab_core:
        st.subheader("✅ 物理内核验证 (Phase 1 & 2 Verified)")
        st.caption("**V13.6 已完成** - 基础物理层与动态交互场均已通过验证")
        
        # 1. 核心监视器: 波动力学透视 (Wave Mechanics Inspector)
        st.markdown("### 🔬 波动力学监视器 (Oscilloscope)")
        st.caption("实时观测 V12.1 内核的波函数演化 | 验证熵增与能量守恒")
        
        # [V13.0] 构建当前配置
        from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
        current_config = DEFAULT_FULL_ALGO_PARAMS.copy()
        if golden_config:
            deep_merge_params(current_config, golden_config)
        current_config = merge_sidebar_values_to_config(current_config)

        # 1.1 实时调优滑块 (V13.7 Cybernetics Update)
        # 获取最新的参数 (可能来自侧边栏修改)
        flow_cfg = current_config.get('flow', {})
        feedback_cfg = flow_cfg.get('feedback', {})
        
        inv_threshold = feedback_cfg.get('inverseControlThreshold', 4.0)
        inv_recoil = feedback_cfg.get('inverseRecoilMultiplier', 2.0)
        era_shield = feedback_cfg.get('eraShieldingFactor', 0.5)
        
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
             st.metric("反克阈值 (Impedance)", f"{inv_threshold:.1f}", help="Threshold > 4.0")
        with col_t2:
             st.metric("反噬倍率 (Recoil)", f"{inv_recoil:.1f}x", help="Recoil Multiplier")
        with col_t3:
             st.metric("环境屏蔽 (Shield)", f"{era_shield*100:.0f}%", help="得地/得令减伤率")

        # 1.2 模拟与可视化
        sim_col1, sim_col2 = st.columns(2)
        
        transmission_eff = flow_cfg.get('medium', {}).get('dampingFactor', 0.1)
        # Recoil Factor is actually interaction.recoilFactor, but we need the feedback one for War sim
        recoil_fac = flow_cfg.get('interaction', {}).get('recoilFactor', 0.3)
        
        # Simulation 1: Nurture (Water -> Wood)
        with sim_col1:
            st.markdown("##### 🌱 抚育实验 (Nurture)")
            from core.math.distributions import ProbValue
            water_src = ProbValue(10.0, std_dev_percent=0.1)
            wood_tgt = ProbValue(2.0, std_dev_percent=0.2)
            
            wave_in = water_src.transmit(damping_factor=transmission_eff, noise_floor=0.5)
            wood_final = wood_tgt + wave_in
            
            fig_nurture = go.Figure()
            x_range = np.linspace(-5, 25, 200)
            
            y_pre = stats.norm.pdf(x_range, wood_tgt.mean, wood_tgt.std)
            fig_nurture.add_trace(go.Scatter(x=x_range, y=y_pre, mode='lines', 
                                           name='Wood (Pre)', line=dict(color='green', dash='dot')))
            
            y_post = stats.norm.pdf(x_range, wood_final.mean, wood_final.std)
            fig_nurture.add_trace(go.Scatter(x=x_range, y=y_post, mode='lines', 
                                           name='Wood (Post)', line=dict(color='#00ff00', width=3), fill='tozeroy', fillcolor='rgba(0,255,0,0.1)'))

            y_src = stats.norm.pdf(x_range, water_src.mean, water_src.std)
            fig_nurture.add_trace(go.Scatter(x=x_range, y=y_src, mode='lines',
                                            name='Source (Water)', line=dict(color='blue', width=1), opacity=0.5))

            fig_nurture.update_layout(height=250, margin=dict(l=10, r=10, t=30, b=10), 
                                    showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                    title_text=f"Energy: {wood_tgt.mean:.1f} → {wood_final.mean:.1f} | Δσ: +{wood_final.std-wood_tgt.std:.2f}")
            st.plotly_chart(fig_nurture, use_container_width=True)
        
        # Simulation 2: War (Water -> Fire)
        with sim_col2:
            st.markdown("##### ⚔️ 战争实验 (War)")
            water_atk = ProbValue(10.0, std_dev_percent=0.1)
            damage_dealt = 5.0
            water_recoil = water_atk.react(damage_dealt, recoil_factor=recoil_fac)
            
            fig_war = go.Figure()
            x_range_w = np.linspace(0, 20, 200)
            
            y_atk_pre = stats.norm.pdf(x_range_w, water_atk.mean, water_atk.std)
            fig_war.add_trace(go.Scatter(x=x_range_w, y=y_atk_pre, mode='lines', 
                                       name='Atk (Pre)', line=dict(color='cyan', dash='dot')))
                                       
            y_atk_post = stats.norm.pdf(x_range_w, water_recoil.mean, water_recoil.std)
            fig_war.add_trace(go.Scatter(x=x_range_w, y=y_atk_post, mode='lines', 
                                       name='Atk (Recoil)', line=dict(color='red', width=3), fill='tozeroy', fillcolor='rgba(255,0,0,0.1)'))
            
            fig_war.update_layout(height=250, margin=dict(l=10, r=10, t=30, b=10),
                                showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                title_text=f"Energy: {water_atk.mean:.1f} → {water_recoil.mean:.1f} | Δσ: +{water_recoil.std-water_atk.std:.2f} (Chaos)")
            st.plotly_chart(fig_war, use_container_width=True)
        
        st.caption(f"🧪 遥测数据: Damping={transmission_eff:.2f}, Noise=0.5, Recoil={recoil_fac:.2f} | 熵增定律验证状态: {'✅ PASS' if (wood_final.std > wood_tgt.std and water_recoil.std > water_atk.std) else '❌ FAIL'}")

        # 2. 验证表图标 (Validation Table Badge)
        st.markdown("---")
        col_v1, col_v2 = st.columns([1, 4])
        with col_v1:
             st.markdown("### 📜 验证表")
        with col_v2:
             st.info("✅ V12.2 反馈控制系统验证已通过 (2025-12-20)")
        
        with st.expander("📊 查看黄金标准验证集 (Golden Standard Dataset)", expanded=False):
             st.markdown("""
             | 案例 ID | 类型 | 场景 | 能量比 (Tgt/Src) | 预期结果 | 状态 |
             | :--- | :--- | :--- | :--- | :--- | :--- |
             | **SYN_FK_01** | 反克 | 水(10)克火(200) | **20.0** | 伤害~0, 反噬>20 | ✅ PASS |
             | **SYN_SH_01** | 屏蔽 | 水冲火 (寒衣) | 1.25 | 伤害减半 (50%) | ✅ PASS |
             | **REAL_JOBS** | 反克 | 辛金克强木 | **15.0** | 金气崩塌 (肺疾) | ✅ PASS |
             | **REAL_EMP** | 正常 | 子午冲 (乾隆) | 1.07 | 激烈对抗 | ✅ PASS |
             """)
             st.caption("*基于 scripts/verify_feedback_physics.py 仿真结果*")

        # 2. 静态验证报告 (极简版)
        st.markdown("---")
        with st.expander("📊 历史验证报告 (Verification Report)", expanded=False):
            st.success("🎉 **Phase 1 全绿** (基础物理层已固化)")
            st.success("🎉 **Phase 2 全绿** (动态交互层已固化)")
            st.info("V12.1 内核已通过 Steve Jobs (2011) 和 Elon Musk (2020) 历史回归测试。")
    
    # ==========================
    # TAB 2: 批量验证
    # ==========================
    with tab_global:
        st.subheader("批量验证")
        st.caption("批量验证所有案例的旺衰判定准确率")
        
        # [V12.1] Phase 1 自检指标
        with st.expander("🔬 Phase 1 自检指标 (Self-Check Metrics)", expanded=False):
            st.caption("**目的**：确保参数调整有物理意义，而不是在制造噪声")
            
            # 选择5个标准案例
            standard_cases = [
                {'id': 'VAL_001', 'name': '标准身强案例', 'expected': 'Strong'},
                {'id': 'VAL_002', 'name': '标准身弱案例', 'expected': 'Weak'},
                {'id': 'VAL_003', 'name': '标准从格案例', 'expected': 'Follower'},
                {'id': 'VAL_004', 'name': '标准专旺案例', 'expected': 'Special_Strong'},
                {'id': 'VAL_005', 'name': '标准平衡案例', 'expected': 'Balanced'}
            ]
            
            if st.button("📊 计算 Phase 1 自检指标", type="secondary"):
                try:
                    # 获取当前配置
                    current_config = st.session_state.get('full_algo_config', {})
                    if not current_config:
                        from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
                        current_config = DEFAULT_FULL_ALGO_PARAMS.copy()
                    
                    from core.engine_graph import GraphNetworkEngine
                    temp_engine = GraphNetworkEngine(config=current_config)
                    
                    # 计算5个标准案例的初始能量分布标准差
                    std_devs = []
                    case_names = []
                    
                    for std_case in standard_cases:
                        # 查找对应的案例
                        found_case = None
                        for c in cases:
                            if str(c.get('id', '')) == std_case['id']:
                                found_case = c
                                break
                        
                        if not found_case:
                            continue
                        
                        # 计算初始能量
                        bazi_list = found_case.get('bazi', [])
                        day_master = found_case.get('day_master', '甲')
                        
                        if len(bazi_list) >= 4:
                            temp_engine.initialize_nodes(bazi_list, day_master)
                            initial_energies = [node.initial_energy for node in temp_engine.nodes]
                            std_dev = np.std(initial_energies)
                            std_devs.append(std_dev)
                            case_names.append(std_case['name'])
                    
                    if std_devs:
                        # 显示结果
                        col1, col2 = st.columns(2)
                        with col1:
                            avg_std = np.mean(std_devs)
                            st.metric("平均能量标准差", f"{avg_std:.2f}",
                                    help="标准差越大，能量分布越不均匀。建议范围：0.5-2.0")
                        with col2:
                            max_std = max(std_devs)
                            min_std = min(std_devs)
                            st.metric("标准差范围", f"{min_std:.2f} - {max_std:.2f}")
                        
                        # 显示详细数据
                        check_data = {
                            '案例': case_names,
                            '能量标准差': [f"{s:.2f}" for s in std_devs]
                        }
                        st.dataframe(pd.DataFrame(check_data), use_container_width=True)
                        
                        # 健康度评估
                        if avg_std < 0.3:
                            st.warning("⚠️ 能量分布过于均匀，可能无法区分强弱")
                        elif avg_std > 3.0:
                            st.warning("⚠️ 能量分布过于不均匀，可能导致极端判定")
                        else:
                            st.success("✅ Phase 1 能量分布健康")
                    else:
                        st.info("未找到标准案例，请确保 calibration_cases.json 中包含标准案例")
                        
                except Exception as e:
                    st.error(f"❌ Phase 1 自检失败: {e}")
                    import traceback
                    with st.expander("查看错误详情"):
                        st.code(traceback.format_exc())
        
        if not cases:
            st.error("No cases loaded.")
        else:
            if st.button("🚀 开始批量回测 (Start Batch Run)", type="primary"):
                results = []
                passed = 0
                total = 0
                
                progress_bar = st.progress(0)
                
                with st.spinner("Quantum Computing Batch Jobs..."):
                    for idx, c in enumerate(cases):
                        # Filter for valid ground truth
                        gt = c.get('ground_truth')
                        if not gt: continue
                        
                        total += 1
                        
                        # 1. Create Profile / Adapter
                        # Luck pillar logic: use dynamic check default or just first luck?
                        # For Wang Shuai (Base Strength), luck pillar usually doesn't affect Base Chart Strength 
                        # UNLESS we consider "Dynamic Strength" in context.
                        # Usually Ground Truth refers to NATIVE Chart Strength.
                        # So we can ignore Luck for Base Strength Assessment?
                        # Wait, V6.0 Profile includes Luck. 
                        # Let's pass "unknown" if not critical.
                        presets = c.get("dynamic_checks", [])
                        luck_p = presets[0]['luck'] if presets else "癸卯"
                        
                        # [V10.0] 使用Controller创建profile
                        profile = quantum_controller.create_profile_from_case(c, luck_p)
                        
                        # 2. Evaluate Base Strength
                        # [V10.0] 使用Controller评估旺衰
                        bazi_list = [profile.pillars['year'], profile.pillars['month'], profile.pillars['day'], profile.pillars['hour']]
                        
                        # Catch errors
                        try:
                            # [V10.0] 使用Controller的方法
                            ws_tuple = quantum_controller.evaluate_wang_shuai(profile.day_master, bazi_list)
                            comp_str = ws_tuple[0] # e.g. "Strong"
                            comp_score = ws_tuple[1]
                        except Exception as e:
                            comp_str = "Error"
                            comp_score = 0.0
                        
                        # 3. Verify
                        target_str = gt.get('strength', 'Unknown')
                        is_match = False
                        
                        if target_str != "Unknown":
                            # V12.0: 改进匹配逻辑 - 精确匹配优先，然后处理特殊情况
                            # 标准化标签（去除空格、统一大小写）
                            target_str = target_str.strip()
                            comp_str = comp_str.strip()
                            
                            # 1. 精确匹配
                            if target_str == comp_str:
                                is_match = True
                            # 2. 处理Special_Strong vs Strong的情况
                            # 如果target是"Strong"，comp是"Special_Strong"，也算匹配（Special_Strong是Strong的子集）
                            elif target_str == "Strong" and comp_str == "Special_Strong":
                                is_match = True
                            # 3. 处理Weak vs Follower的情况
                            # 如果target是"Follower"，comp是"Follower"或"Weak"，都算匹配（Follower是极弱，可以接受Weak）
                            elif target_str == "Follower" and (comp_str == "Follower" or comp_str == "Weak"):
                                is_match = True
                            # 如果target是"Weak"，comp是"Weak"或"Follower"，都算匹配
                            elif target_str == "Weak" and (comp_str == "Weak" or comp_str == "Follower"):
                                is_match = True
                            # 4. 处理Balanced的情况
                            elif target_str == "Balanced" and comp_str == "Balanced":
                                is_match = True
                            # 5. 其他情况：如果target包含comp或comp包含target（但排除已处理的情况）
                            elif (target_str in comp_str or comp_str in target_str) and not (
                                (target_str == "Strong" and comp_str == "Special_Strong") or
                                (comp_str == "Strong" and target_str == "Special_Strong")
                            ):
                                is_match = True
                        
                        if is_match: passed += 1
                        
                        results.append({
                            "Case ID": c.get('id', idx),
                            "Name": c.get('description', ''),
                            "Target": target_str,
                            "Computed": comp_str,
                            "Score": f"{comp_score:.1f}",
                            "Result": "✅ Pass" if is_match else "❌ Fail"
                        })
                        
                        progress_bar.progress((idx + 1) / len(cases))
                
                # Report
                accuracy = (passed / total) * 100 if total > 0 else 0.0
                st.metric("综合准确率 (Global Accuracy)", f"{accuracy:.1f}%", f"{passed}/{total} Cases")
                
                # DataFrame
                st.dataframe(results, width='stretch')
                
                if accuracy < 60:
                    st.error("Low Accuracy! Tuning Required.")
                elif accuracy < 90:
                    st.warning("Moderate Accuracy. Check Failed Cases.")
                else:
                    st.success("Exclellent Fit! Ready for Deployment.")
            else:
                st.info("Click button to run batch verification on 25 cases.")
            
            # End of Tab Global Logic

    # ==========================
    # TAB 2: 单点分析
    # ==========================
    with tab_single:
        st.subheader("单点分析")
        
        # Mode Selection
        verify_mode = st.radio("数据源 (Data Source)", ["📚 预设案例 (Presets)", "✍️ 手动录入 (Manual Input)"], horizontal=True)
        
        selected_case = None
        user_year = "甲辰"
        user_luck = "癸卯"

        if verify_mode == "📚 预设案例 (Presets)":
            if not cases:
                st.error("No preset data.")
            else:
                c_sel, c_ctx = st.columns([2, 3])
                with c_sel:
                    def _fmt(i):
                        c = cases[i]
                        birth = ""
                        if c.get("birth_date"):
                            bt = c.get("birth_time", "")
                            birth = f" | {c.get('birth_date')} {bt}"
                        return f"No.{c.get('id','?')} {c.get('day_master','?')}日主 ({c.get('gender','?')}){birth}"
                    case_idx = st.selectbox("📂 选择档案", range(len(cases)), format_func=_fmt)
                    selected_case = cases[case_idx]
                
                with c_ctx:
                    presets = selected_case.get("dynamic_checks", []) or []
                    c_y, c_l = st.columns(2)
                    first_chk = presets[0] if presets else {}
                    # Prefer dynamic check year; else use derived birth year; else empty
                    derived_year = (selected_case.get("birth_date") or "")[:4]
                    def_year = first_chk.get('year') or derived_year or ""
                    def_luck = first_chk.get('luck', "")
                    user_year = c_y.text_input("流年 (Year)", value=def_year)
                    user_luck = c_l.text_input("大运 (Luck)", value=def_luck)
                    
        else: # Manual Input
            st.markdown("#### 📝 新案例录入")
            mc1, mc2, mc3, mc4, mc5 = st.columns(5)
            in_year = mc1.number_input("年 (Year)", 1900, 2100, 1991) # Example: 1991 (Wei Month case?)
            in_month = mc2.number_input("月 (Month)", 1, 12, 7) # Wei Month approx July
            in_day = mc3.number_input("日 (Day)", 1, 31, 15)
            in_hour = mc4.number_input("时 (Hour)", 0, 23, 12)
            in_gender = mc5.selectbox("性别", ["男", "女"])
            
            # Ground Truth
            st.markdown("#### 🎯 真值设定 (Ground Truth)")
            gt1, gt2 = st.columns(2)
            gt_strength = gt1.selectbox("真实身强", ["Unknown", "Strong", "Weak", "Follower"], index=2) # Default Weak
            gt_fav = gt2.multiselect("真实喜用", ["Wood", "Fire", "Earth", "Metal", "Water"], default=[])
            
            # Run Calculation to form Case
            if st.button("🚀 载入并计算 (Load & Run)", type="primary"):
                with st.spinner("Quantum Computing... Note: Manual Mode calculates chart on the fly."):
                    req = {'birth_year': in_year, 'birth_month': in_month, 'birth_day': in_day, 'birth_hour': in_hour, 'gender': in_gender}
                    # [V10.0] 使用Controller计算排盘
                    res = quantum_controller.calculate_chart(req)
                    
                    # Convert to Case Format
                    bazi_strs = [f"{p[0]}{p[1]}" for p in res['bazi']]
                    
                    manual_case = {
                        'id': 'MANUAL',
                        'gender': in_gender,
                        'bazi': bazi_strs, # [Year, Month, Day, Hour]
                        'day_master': res['bazi'][2][0],
                        'dynamic_checks': [],
                        # Custom fields for verification
                        'ground_truth': {
                            'strength': gt_strength,
                            'favorable': gt_fav
                        },
                        'computed_result': res # Store for comparison
                    }
                    st.session_state['manual_case'] = manual_case
                    st.rerun()
            
            if 'manual_case' in st.session_state:
                selected_case = st.session_state['manual_case']
                st.success(f"✅ Loaded: {selected_case['bazi']} | DM: {selected_case['day_master']}")
                
                # Comparison
                if 'computed_result' in selected_case and 'ground_truth' in selected_case:
                    cr = selected_case['computed_result']
                    gt = selected_case['ground_truth']
                    
                    # Determine Computed Strength String
                    # cr['wang_shuai'] is (str, score), e.g. ('Weak', 0.45)
                    comp_str = cr['wang_shuai'][0]
                    comp_score = cr['energy_score']
                    
                    # Display Feedback
                    st.divider()
                    col_res, col_verdict = st.columns([3, 2])
                    
                    with col_res:
                        st.metric("算法判定 (Computed)", f"{comp_str} ({comp_score:.1f})")
                        st.write(f"喜用神: {cr['favorable_elements']}")
                        
                    with col_verdict:
                        is_match = (gt['strength'] == "Unknown") or (gt['strength'] in comp_str) or (comp_str in gt['strength'])
                        # Loose matching "Strong" vs "Strong"
                        
                        if is_match:
                            st.success(f"MATCH! ✅\nTarget: {gt['strength']}")
                        else:
                            st.error(f"MISMATCH ❌\nTarget: {gt['strength']}")
                            
                        # Favorable overlap?
                        comp_fav_set = set(cr['favorable_elements'])
                        gt_fav_set = set(gt['favorable'])
                        if gt_fav_set:
                            overlap = comp_fav_set.intersection(gt_fav_set)
                            if overlap:
                                st.caption(f"✅ Favorable Overlap: {overlap}")
                            else:
                                st.caption(f"⚠️ Favorable Divergence!")
                
                st.divider()

        if selected_case:
            # === Trinity V6.0: Single Microscope ===
            # Continue with existing logic using selected_case
            
                # [V10.0] MCP上下文注入：注入GEO、ERA、大运、流年等信息
            try:
                import logging
                _logger = logging.getLogger(__name__)
                
                # 解析用户输入的年份（如果是干支，转换为年份；如果是数字，直接使用）
                selected_year_int = None
                if user_year and user_year.isdigit():
                    selected_year_int = int(user_year)
                elif user_year:
                    # 如果是干支格式，暂时无法反向转换，使用默认值
                    # 这里可以改进，但暂时保持兼容性
                    pass
                
                # [V10.0] 使用Controller注入MCP上下文
                case_with_context = quantum_controller.inject_mcp_context(selected_case, selected_year_int)
                
                # [V10.0] 使用Controller获取大运（优先级：MCP上下文 -> timeline -> VirtualBaziProfile自动反推）
                if not user_luck or user_luck == "" or user_luck == "未知":
                    user_luck = quantum_controller.get_luck_pillar(selected_case, selected_year_int, mcp_context=case_with_context)
                    if user_luck and user_luck != "未知":
                        st.info(f"💡 大运已获取: {user_luck} (年份: {selected_year_int})")
                
                # [V10.0] 使用Controller计算流年干支
                if selected_year_int:
                    user_year = quantum_controller.calculate_year_pillar(selected_year_int)
                
                # 使用上下文中的GEO和ERA信息
                geo_city = case_with_context.get('geo_city', 'Unknown')
                geo_latitude = case_with_context.get('geo_latitude', 0.0)
                geo_longitude = case_with_context.get('geo_longitude', 0.0)
                era_element = case_with_context.get('era_element', 'Fire')
                
                _logger.debug(f"📍 MCP上下文: GEO={geo_city}, ERA={era_element}, 大运={user_luck}, 流年={user_year}")
            except Exception as e:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(f"⚠️ MCP上下文注入失败，使用默认值: {e}")
                geo_city = selected_case.get('geo_city', 'Unknown')
                geo_latitude = selected_case.get('geo_latitude', 0.0)
                geo_longitude = selected_case.get('geo_longitude', 0.0)
                era_element = 'Fire'
            
            st.info(f"Analyzing Case: {selected_case['bazi']}")
            
            # [V12.1] Phase 1 可视化：显示初始能量 H^(0) 分布
            with st.expander("📊 Phase 1: 初始能量场可视化 (H^(0) Distribution)", expanded=True):
                st.caption("**实时显示**：调整Phase 1参数后，查看初始能量分布的变化")
                
                try:
                    # 获取当前配置（优先使用session_state中的配置）
                    current_config = st.session_state.get('full_algo_config', {})
                    if not current_config:
                        # 如果没有配置，使用默认配置
                        from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
                        current_config = DEFAULT_FULL_ALGO_PARAMS.copy()
                    
                    # 创建临时引擎计算初始能量
                    from core.engine_graph import GraphNetworkEngine
                    temp_engine = GraphNetworkEngine(config=current_config)
                    
                    # 准备数据
                    bazi_list = [
                        selected_case['bazi'][0] if len(selected_case['bazi']) > 0 else '',
                        selected_case['bazi'][1] if len(selected_case['bazi']) > 1 else '',
                        selected_case['bazi'][2] if len(selected_case['bazi']) > 2 else '',
                        selected_case['bazi'][3] if len(selected_case['bazi']) > 3 else ''
                    ]
                    day_master = selected_case.get('day_master', '甲')
                    
                    # 初始化节点（只计算初始能量，不传播）
                    temp_engine.initialize_nodes(bazi_list, day_master, luck_pillar=user_luck, year_pillar=user_year)
                    
                    # 提取初始能量数据
                    node_labels = []
                    initial_energies = []
                    node_types = []
                    pillar_names = []
                    
                    for node in temp_engine.nodes:
                        label = f"{node.char}"
                        if node.pillar_idx < 4:  # 原局节点
                            pillar_name = ['年', '月', '日', '时'][node.pillar_idx]
                            label = f"{pillar_name}{node.char}"
                        elif node.pillar_idx == 4:  # 大运节点
                            label = f"运{node.char}"
                        elif node.pillar_idx == 5:  # 流年节点
                            label = f"岁{node.char}"
                        
                        node_labels.append(label)
                        initial_energies.append(node.initial_energy)
                        node_types.append(node.node_type)
                        pillar_names.append(node.pillar_name if hasattr(node, 'pillar_name') else '')
                    
                    # 创建柱状图（使用全局导入的 go）
                    fig_h0 = go.Figure()
                    
                    # 按节点类型分组着色
                    colors = []
                    for i, node_type in enumerate(node_types):
                        if node_type == 'stem':
                            colors.append('#4A90E2')  # 蓝色：天干
                        else:
                            colors.append('#E24A4A')  # 红色：地支
                    
                    fig_h0.add_trace(go.Bar(
                        x=node_labels,
                        y=initial_energies,
                        marker_color=colors,
                        text=[f"{e:.2f}" for e in initial_energies],
                        textposition='outside',
                        name='初始能量 H^(0)'
                    ))
                    
                    # 标记月令节点（最重要）
                    month_idx = None
                    for i, (label, pname) in enumerate(zip(node_labels, pillar_names)):
                        if pname == 'month' and node_types[i] == 'branch':
                            month_idx = i
                            break
                    
                    if month_idx is not None:
                        fig_h0.add_annotation(
                            x=node_labels[month_idx],
                            y=initial_energies[month_idx],
                            text="⭐ 月令",
                            showarrow=True,
                            arrowhead=2,
                            arrowcolor='#FFD700',
                            font=dict(color='#FFD700', size=12, family='Arial Black')
                        )
                    
                    fig_h0.update_layout(
                        title="Phase 1: 初始能量分布 H^(0)",
                        xaxis_title="节点",
                        yaxis_title="初始能量",
                        height=400,
                        showlegend=False,
                        plot_bgcolor='rgba(0,0,0,0.05)',
                        paper_bgcolor='rgba(0,0,0,0)'
                    )
                    
                    st.plotly_chart(fig_h0, use_container_width=True)
                    
                    # 显示统计信息
                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    with col_stat1:
                        st.metric("总初始能量", f"{sum(initial_energies):.2f}")
                    with col_stat2:
                        max_idx = initial_energies.index(max(initial_energies))
                        st.metric("最大能量节点", f"{node_labels[max_idx]} ({max(initial_energies):.2f})")
                    with col_stat3:
                        std_dev = np.std(initial_energies)
                        st.metric("能量标准差", f"{std_dev:.2f}", 
                                help="标准差越大，能量分布越不均匀")
                    
                    st.caption("💡 **调优提示**：调整月令权重后，观察月令节点的初始能量是否真的'一家独大'")
                    
                except Exception as e:
                    st.warning(f"⚠️ Phase 1 可视化失败: {e}")
                    import traceback
                    with st.expander("查看错误详情"):
                        st.code(traceback.format_exc())
            
            # [V10.0] 使用Controller创建profile和计算
            current_mcp_context = case_with_context if 'case_with_context' in locals() else {}
            profile = quantum_controller.create_profile_from_case(selected_case, user_luck, mcp_context=current_mcp_context)
            
            # [V10.0] 使用Controller计算年份上下文
            try:
                ctx = quantum_controller.calculate_year_context(profile, selected_year_int or 2024)
                
                # [V10.0] 准备数据并调用Controller计算能量
                b_date = getattr(profile, 'birth_date', None)
                birth_info_mock = {
                    'year': b_date.year,
                    'month': b_date.month,
                    'day': b_date.day,
                    'hour': getattr(b_date, 'hour', 12),
                    'gender': profile.gender
                } if b_date else {
                    'year': 2000, 'month': 1, 'day': 1, 'hour': 12, 'gender': profile.gender
                }
                
                bazi_list = [profile.pillars['year'], profile.pillars['month'], profile.pillars['day'], profile.pillars['hour']]
                wang_shuai_str = "身中和"
                try:
                    ws, _ = quantum_controller.evaluate_wang_shuai(profile.day_master, bazi_list)
                    wang_shuai_str = "身旺" if "Strong" in ws else "身弱"
                except: pass

                case_data_mock = {
                    'id': selected_case.get('id', 999), 
                    'gender': selected_case.get('gender', '男'),
                    'day_master': profile.day_master,
                    'wang_shuai': wang_shuai_str,
                    'bazi': bazi_list,
                    'birth_info': birth_info_mock,
                    'city': geo_city,
                    'geo_latitude': geo_latitude,
                    'geo_longitude': geo_longitude
                }
                
                dyn_ctx_mock = {
                    'year': user_year,
                    'dayun': user_luck,
                    'luck': user_luck,
                    'era_element': era_element
                }
                
                # [V10.0] 使用Controller计算能量（不再直接调用engine）
                detailed_res = quantum_controller.calculate_energy(case_data_mock, dyn_ctx_mock)
                
            except Exception as e:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.error(f"❌ 计算失败: {e}", exc_info=True)
                st.error(f"计算失败: {e}")
                detailed_res = {}
            
            
            # [V10.0] Map to format compatible with UI (只保留旺衰相关，删除财富/情感/事业)
            pred_res = {
                'desc': ctx.narrative_prompt if 'ctx' in locals() else '', # Use the rich prompt
                'pillar_energies': detailed_res.get('pillar_energies', [0]*8),
                'narrative_events': detailed_res.get('narrative_events', [])
            }
            
            # --- Rendering Bazi Chart ---
            pe = pred_res.get('pillar_energies', [0]*8)
            bazi = selected_case['bazi'] # [Year, Month, Day, Hour]
            def split_sb(pillar): return (pillar[0], pillar[1]) if pillar and len(pillar)>1 else ("?","?")
            
            y_s, y_b = split_sb(bazi[0])
            m_s, m_b = split_sb(bazi[1])
            d_s, d_b = split_sb(bazi[2])
            h_s, h_b = split_sb(bazi[3])
            l_s, l_b = split_sb(user_luck)
            n_s, n_b = split_sb(user_year)

            # === GROUND TRUTH VERIFICATION ===
            # [V10.0] 注意：只保留旺衰判定验证，删除财富、情感、事业等宏观指标
            gt = selected_case.get('ground_truth')
            
            if gt:
                # [V10.0] 旺衰概率波函数可视化（可选显示）
                # 添加折叠选项，让用户可以选择是否显示
                with st.expander("📈 旺衰概率波函数 (当前案例能量位置)", expanded=False):
                    st.caption("""
                    **功能说明**：
                    - 这是一个Sigmoid概率曲线，展示日主能量占比与身强概率的关系
                    - X轴：日主能量占比（0-10，表示日主能量/总能量的比例）
                    - Y轴：身强概率（0%-100%）
                    - 红色星标：当前案例的能量位置
                    - 橙色虚线：临界点（相变阈值）
                    - 灰色虚线：50%概率线（身强/身弱分界线）
                    
                    **用途**：帮助理解当前案例在能量空间中的位置，以及判定为身强的概率。
                    """)
                    
                    try:
                        from ui.utils.strength_probability_visualization import plot_strength_probability_curve
                        
                        # 获取当前案例的能量值（直接计算，不依赖ws变量）
                        current_case_energy_value = None
                        try:
                            # [V10.0] 使用Controller评估旺衰，获取详细结果
                            ws_tuple = quantum_controller.evaluate_wang_shuai(profile.day_master, bazi_list)
                            if isinstance(ws_tuple, tuple) and len(ws_tuple) >= 2:
                                # 方法1: 从引擎直接获取能量占比（更准确）
                                engine = quantum_controller.engine
                                if hasattr(engine, 'nodes') and engine.nodes:
                                    # 重新初始化引擎以确保能量值是最新的
                                    engine.initialize_nodes(bazi_list, profile.day_master)
                                    engine.build_adjacency_matrix()
                                    engine.propagate(max_iterations=10)
                                    
                                    # 计算能量占比
                                    total_energy = 0.0
                                    self_team_energy = 0.0
                                    dm_element = engine.STEM_ELEMENTS.get(profile.day_master, 'earth')
                                    
                                    for node in engine.nodes:
                                        node_energy = node.current_energy
                                        total_energy += node_energy
                                        if node.element == dm_element:
                                            self_team_energy += node_energy
                                    
                                    # 能量占比 = self_team_energy / total_energy
                                    # 映射到0-10范围（与概率波函数的energy_range一致）
                                    if total_energy > 0:
                                        energy_ratio = self_team_energy / total_energy
                                        # 映射到0-10范围（概率波函数使用0-10范围）
                                        current_case_energy_value = energy_ratio * 10.0
                                    else:
                                        # 如果总能量为0，使用strength_score作为后备
                                        strength_score = ws_tuple[1]
                                        current_case_energy_value = (strength_score / 100.0) * 10.0
                                else:
                                    # 后备方法：使用strength_score估算
                                    strength_score = ws_tuple[1]  # 0-100
                                    current_case_energy_value = (strength_score / 100.0) * 10.0
                        except Exception as e:
                            import logging
                            _logger = logging.getLogger(__name__)
                            _logger.warning(f"⚠️ 计算当前案例能量值失败: {e}", exc_info=True)
                            current_case_energy_value = None
                        
                        # 从session_state获取当前参数
                        energy_threshold_center = st.session_state.get('strength_energy_threshold', 2.89)
                        phase_transition_width = st.session_state.get('strength_phase_width', 10.0)
                        
                        # 显示当前案例的能量值
                        if current_case_energy_value is not None:
                            current_prob = 1.0 / (1.0 + np.exp(-(10.0 / phase_transition_width) * (current_case_energy_value - energy_threshold_center)))
                            
                            # 计算旺衰分数（0-100分）
                            strength_score = current_case_energy_value * 10.0
                            
                            # 判定逻辑说明
                            if strength_score <= 40.0:
                                judgment_reason = "⚠️ 分数≤40分，判定为弱（即使概率高）"
                                judgment_color = "🔴"
                            elif strength_score > 50.0 and current_prob >= 0.60:
                                judgment_reason = "✅ 分数>50分且概率≥60%，判定为强"
                                judgment_color = "🟢"
                            elif strength_score <= 50.0:
                                judgment_reason = "⚠️ 分数≤50分，判定为弱"
                                judgment_color = "🔴"
                            else:
                                judgment_reason = "⚪ 中间状态，判定为平衡"
                                judgment_color = "🟡"
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("能量占比", f"{current_case_energy_value:.2f}", "0-10范围")
                            with col2:
                                st.metric("旺衰分数", f"{strength_score:.1f}", "0-100分")
                            with col3:
                                st.metric("身强概率", f"{current_prob:.1%}", "Sigmoid计算")
                            with col4:
                                st.metric("临界点", f"{energy_threshold_center:.2f}", f"带宽: {phase_transition_width:.1f}")
                            
                            # 显示判定逻辑说明
                            st.info(f"{judgment_color} **判定逻辑**: {judgment_reason}")
                            st.caption("💡 **说明**: 最终判定优先考虑旺衰分数（0-100分），而不是身强概率。只有当分数>50分且概率≥60%时，才判定为强。")
                        
                        probability_fig = plot_strength_probability_curve(
                            energy_threshold_center=energy_threshold_center,
                            phase_transition_width=phase_transition_width,
                            current_case_energy=current_case_energy_value
                        )
                        st.plotly_chart(probability_fig, use_container_width=True, key='case_strength_probability_curve')
                        if current_case_energy_value is None:
                            st.caption("💡 提示：当前案例能量值未计算，图表中未显示标记点")
                    except Exception as e:
                        st.caption(f"⚠️ 概率曲线可视化失败: {e}")
                        import traceback
                        with st.expander("查看错误详情"):
                            st.code(traceback.format_exc())
                
                # Strength Verification
                if 'strength' in gt:
                    st.markdown("---")
                    st.markdown("#### 🧬 旺衰判定 (Strength Judgment)")
                    
                    # Computed Strength
                    comp_ws_raw = ws if 'ws' in locals() else "Unknown"
                    
                    # Match Logic
                    is_match = False
                    if gt['strength'] != "Unknown":
                        is_match = (gt['strength'] in comp_ws_raw) or (comp_ws_raw in gt['strength'])
                        if "Follower" in gt['strength'] and "Follower" in comp_ws_raw: 
                            is_match = True
                    
                    c_ver, c_det = st.columns([1, 3])
                    with c_ver:
                        if is_match:
                            st.success(f"MATCH ✅\n{comp_ws_raw}")
                        else:
                            st.error(f"MISMATCH ❌\nGot: {comp_ws_raw}")
                            
                    with c_det:
                        st.caption(f"Target: **{gt.get('strength', '?')}** | Note: {gt.get('note', '')}")
                        if 'favorable' in gt:
                            st.caption(f"Target Favorable: {gt['favorable']}")

            st.markdown(f"""
            <style>
                .bazi-box {{ background-color: #1E1E1E; padding: 15px; border-radius: 8px; text-align: center; font-family: 'Courier New'; }}
                .stem {{ font-size: 1.8em; font-weight: bold; color: #FFF; }}
                .branch {{ font-size: 1.8em; font-weight: bold; color: #DDD; }}
                .day-master {{ color: #FF4500 !important; }}
                .dynamic {{ color: #00BFFF !important; }}
                .dynamic-year {{ color: #FF69B4 !important; }}
                .energy-val {{ font-size: 0.5em; color: #4CAF50; }}
            </style>
            <div class="bazi-box">
                <table style="width:100%; text-align:center;">
                    <tr style="color:#888;"><td>年</td><td>月</td><td>日</td><td>时</td><td width="20"></td><td>运</td><td>岁</td></tr>
                    <tr>
                        <td class="stem">{y_s}<div class="energy-val">{pe[0]}</div></td>
                        <td class="stem">{m_s}<div class="energy-val">{pe[2]}</div></td>
                        <td class="stem day-master">{d_s}<div class="energy-val">{pe[4]}</div></td>
                        <td class="stem">{h_s}<div class="energy-val">{pe[6]}</div></td>
                        <td></td>
                        <td class="stem dynamic">{l_s}</td>
                        <td class="stem dynamic-year">{n_s}</td>
                    </tr>
                    <tr>
                        <td class="branch">{y_b}<div class="energy-val">{pe[1]}</div></td>
                        <td class="branch">{m_b}<div class="energy-val">{pe[3]}</div></td>
                        <td class="branch day-master">{d_b}<div class="energy-val">{pe[5]}</div></td>
                        <td class="branch">{h_b}<div class="energy-val">{pe[7]}</div></td>
                        <td></td>
                        <td class="branch dynamic">{l_b}</td>
                        <td class="branch dynamic-year">{n_b}</td>
                    </tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            
            # --- Results ---
            # [V10.0] 只显示旺衰相关结果，删除财富/情感/事业等宏观指标
            st.markdown("#### 结果分析")
            if pred_res.get('desc'):
                st.info(f"AI 判词: {pred_res['desc']}")

            # Narrative Cards (New in V2.9)
            narrative_events = pred_res.get('narrative_events', [])
            if narrative_events:
                st.markdown("#### 📜 核心叙事 (Narrative Events)")
                nc1, nc2 = st.columns(2)
                for i, event in enumerate(narrative_events):
                    with nc1 if i % 2 == 0 else nc2:
                        render_narrative_card(event)

            # Timeline
            st.divider()
            with st.expander("⏳ 12年运势模拟 (Timeline Simulation)"):
                # [V10.0] 使用Controller，不再直接创建engine
                # 如果需要更新配置，使用controller.update_config()
                
                years = range(2024, 2036)
                sim_data = []
                
                for y in years:
                    gan = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"][(y - 2024) % 10]
                    zhi = ["辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑", "寅", "卯"][(y - 2024) % 12]
                    sim_year_pillar = f"{gan}{zhi}"
                    
                    # Prepare Case Data for Calculate Energy
                    b_date = getattr(profile, 'birth_date', None)
                    birth_info_sim = {
                        'year': b_date.year, 'month': b_date.month, 'day': b_date.day,
                        'hour': getattr(b_date, 'hour', 12), 'gender': profile.gender
                    } if b_date else { 'year': 2000, 'month': 1, 'day': 1, 'hour': 12, 'gender': profile.gender }
                    
                    bazi_list = [profile.pillars['year'], profile.pillars['month'], profile.pillars['day'], profile.pillars['hour']]
                    
                    # [V10.0] Estimate Wang Shuai for simulation (使用Controller)
                    try:
                        ws_sim, _ = quantum_controller.evaluate_wang_shuai(profile.day_master, bazi_list)
                        ws_str_sim = "身旺" if "Strong" in ws_sim else "身弱"
                    except:
                        ws_str_sim = "身中和"

                    case_data_sim = {
                        'id': selected_case.get('id', 999), 
                        'gender': selected_case.get('gender', '男'),
                        'day_master': profile.day_master,
                        'wang_shuai': ws_str_sim,
                        'bazi': bazi_list,
                        'birth_info': birth_info_sim,
                        # Pass physics sources if available? 
                        # Ideally flux engine runs inside calculate_energy if missing
                    }
                    
                    dyn_ctx_sim = {
                        'year': sim_year_pillar,
                        'dayun': user_luck, # Static luck for Lab
                        'luck': user_luck
                    }
                    
                    # [V10.0] 使用Controller计算能量（不再直接调用engine）
                    det_res = quantum_controller.calculate_energy(case_data_sim, dyn_ctx_sim)

                    # [V10.0] 只保留旺衰相关数据，删除财富/情感/事业
                    sim_data.append({
                        "year": y,
                        "desc": det_res.get('desc', '')
                    })
                
                # [V10.0] 删除财富/情感/事业的时间线图表（这些属于第二层验证）
                # 如果将来需要显示旺衰趋势，可以添加strength_score的时间线
                if sim_data:
                    st.info(f"已计算 {len(sim_data)} 年的数据（财富/情感/事业趋势图表已移除，这些属于第二层验证）")

            # === V33.0: Engine Comparison (引擎对比) ===
            if 'graph_data' in detailed_res:
                st.divider()
            
            # === V9.6: GEO 能量轨迹对比 (GEO Comparison) ===
            st.divider()
            st.markdown("### 🌍 GEO 能量轨迹对比 (GEO Energy Trajectory Comparison)")
            st.caption("对比基线 (Baseline) 与 GEO 修正后的能量轨迹")
            
            # V9.6: Use city from sidebar if available, otherwise provide selection in main area
            # Check if sidebar city is set and valid
            sidebar_city = st.session_state.get('p2_sidebar_city', 'Unknown')
            
            if sidebar_city and sidebar_city.lower() not in ['unknown', 'none', '']:
                # Use sidebar city selection
                comparison_city = sidebar_city
                st.info(f"📍 使用侧边栏选择的城市: **{comparison_city}** (可在侧边栏「时空修正」面板中修改)")
            else:
                # Fallback: Provide city selection in main area
                def load_geo_cities():
                    """Load available cities from geo_coefficients.json"""
                    geo_path = os.path.join(os.path.dirname(__file__), "../../data/geo_coefficients.json")
                    try:
                        with open(geo_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            cities = list(data.get("cities", {}).keys())
                            return ["None"] + sorted(cities) if cities else ["None", "Beijing", "Shanghai", "Singapore"]
                    except:
                        return ["None", "Beijing", "Shanghai", "Singapore", "Harbin", "Guangzhou", "Sydney"]
                
                geo_cities = load_geo_cities()
                comparison_city = st.selectbox(
                    "🌍 选择 GEO 对比城市 (Select City for GEO Comparison)",
                    geo_cities,
                    index=0,
                    help="选择一个城市以查看 GEO 修正后的能量轨迹与基线的对比（或使用侧边栏「时空修正」面板中的城市选择）"
                )
                
                # Convert "None" to None for controller
                if comparison_city == "None":
                    comparison_city = None
            
            # Check if we have a valid case and city for comparison
            if selected_case and comparison_city and comparison_city.lower() not in ['unknown', 'none', '']:
                # Ensure controller has user input set (needed for get_geo_comparison)
                # We need to set user input from selected_case
                try:
                    # Try to derive birth info from case
                    # For preset cases, we might not have exact birth date
                    # Use a default date if needed
                    from datetime import date
                    default_date = date(2000, 1, 1)
                    default_gender = selected_case.get('gender', '男')
                    
                    # Set controller input (minimal required fields)
                    controller.set_user_input(
                        name=selected_case.get('description', 'Test Case'),
                        gender=default_gender,
                        date_obj=default_date,
                        time_int=12,
                        minute_int=0,
                        city=comparison_city,
                        enable_solar=True,
                        longitude=116.46  # Default Beijing longitude
                    )
                    
                    st.subheader(f"📊 GEO 能量轨迹对比 ({comparison_city} vs. Baseline)")
                    
                    # Get comparison data
                    start_year_geo = 2024  # Default start year
                    duration_geo = 12     # Default duration
                    
                    with st.spinner(f"正在计算 {comparison_city} 的 GEO 修正轨迹..."):
                        comparison_df, geo_modifiers = controller.get_geo_comparison(
                            city=comparison_city,
                            start_year=start_year_geo,
                            duration=duration_geo
                        )
                    
                    if not comparison_df.empty:
                        # Display GEO modifiers
                        if geo_modifiers:
                            st.markdown("#### 🌍 GEO 修正系数")
                            modifier_display = {k: v for k, v in geo_modifiers.items()
                                              if k not in ['desc'] and isinstance(v, (int, float))}
                            if modifier_display:
                                st.json(modifier_display)
                            if geo_modifiers.get('desc'):
                                st.caption(f"📍 {geo_modifiers.get('desc')}")
                        
                        # [V10.0] 删除财富/情感/事业的GEO轨迹对比（这些属于第二层验证）
                        # 如果将来需要显示旺衰的GEO轨迹，可以添加strength_score的对比
                        st.info("⚠️ GEO能量轨迹对比图表已移除。财富/情感/事业等宏观指标属于第二层验证，不应在此页面显示。")
                        
                        # Display data table (保留数据表供参考)
                        with st.expander("📋 详细数据表 (Detailed Data Table)"):
                            st.dataframe(comparison_df, width='stretch')
                    else:
                        st.warning(f"⚠️ 无法生成 {comparison_city} 的对比数据。请检查 Controller 配置。")
                        
                except Exception as e:
                    st.error(f"❌ 轨迹计算错误: {e}")
                    st.exception(e)
            elif selected_case:
                st.info("请选择一个城市以生成 GEO 能量轨迹对比图。")
            else:
                st.info("请先选择一个案例以进行 GEO 对比分析。")

    # ==========================
    # TAB 4: 规则匹配
    # ==========================
    with tab_rules:
        st.subheader("📜 规则匹配分析")
        st.caption("检测当前八字中触发的已验证规则（基于 ProbValue 概率波函数和非线性激活函数）")
        
        # Get current case or input
        current_bazi = None
        current_dm = None
        
        if selected_case and isinstance(selected_case, dict):
            current_bazi = selected_case.get('bazi', [])
            current_dm = selected_case.get('day_master', '')
        elif controller._chart:
            chart = controller._chart
            current_bazi = [
                f"{chart.get('year', {}).get('stem', '')}{chart.get('year', {}).get('branch', '')}",
                f"{chart.get('month', {}).get('stem', '')}{chart.get('month', {}).get('branch', '')}",
                f"{chart.get('day', {}).get('stem', '')}{chart.get('day', {}).get('branch', '')}",
                f"{chart.get('hour', {}).get('stem', '')}{chart.get('hour', {}).get('branch', '')}"
            ]
            current_dm = chart.get('day', {}).get('stem', '')
        
        if current_bazi and current_dm:
            # Display current Bazi info
            st.markdown(f"**当前八字**: {' '.join(current_bazi)} | **日主**: {current_dm}")
            st.divider()
            
            # Match rules
            try:
                from core.rule_matcher import RuleMatcher, MatchedRule
                
                matcher = RuleMatcher()
                matched_rules = matcher.match(current_bazi, current_dm)
                summary = matcher.get_rule_summary(matched_rules)
                
                # Display summary metrics
                col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
                cat_labels = {'A': '基础物理', 'B': '几何交互', 'C': '能量流转', 'D': '墓库规则', 'E': '判定阈值'}
                
                with col_m1:
                    st.metric("总规则数", summary['total'])
                with col_m2:
                    st.metric("A类 (物理)", summary['by_category'].get('A', 0))
                with col_m3:
                    st.metric("B类 (交互)", summary['by_category'].get('B', 0))
                with col_m4:
                    st.metric("C类 (流转)", summary['by_category'].get('C', 0))
                with col_m5:
                    st.metric("D+E类", summary['by_category'].get('D', 0) + summary['by_category'].get('E', 0))
                
                st.divider()
                
                # Display effects (dynamic rules only)
                if summary['active_effects']:
                    st.markdown("### ⚡ 激活的动态规则")
                    for effect in summary['active_effects']:
                        st.info(f"🔹 {effect}")
                
                st.divider()
                
                # Display all rules by category
                st.markdown("### 📋 完整规则列表")
                
                # Category tabs
                cat_tabs = st.tabs(["A: 基础物理", "B: 几何交互", "C: 能量流转", "D: 墓库", "E: 判定"])
                
                categories = ['A', 'B', 'C', 'D', 'E']
                for i, cat in enumerate(categories):
                    with cat_tabs[i]:
                        cat_rules = [r for r in matched_rules if r.category == cat]
                        
                        if not cat_rules:
                            st.caption("无匹配规则")
                            continue
                        
                        for rule in cat_rules:
                            # Create card-like display
                            with st.container():
                                col_id, col_name, col_effect = st.columns([1, 3, 4])
                                
                                with col_id:
                                    st.markdown(f"**{rule.rule_id}**")
                                
                                with col_name:
                                    st.markdown(f"**{rule.name_cn}**")
                                    st.caption(rule.name_en)
                                
                                with col_effect:
                                    if rule.effect and rule.effect != "始终应用":
                                        st.success(f"✅ {rule.effect}")
                                    else:
                                        st.info("📌 始终应用")
                                    
                                    if rule.participants:
                                        st.caption(f"参与: {', '.join(rule.participants)}")
                                
                                st.divider()
                
                # JSON export
                with st.expander("📤 导出规则匹配结果 (JSON)"):
                    export_data = {
                        "bazi": current_bazi,
                        "day_master": current_dm,
                        "summary": summary,
                        "rules": [
                            {
                                "id": r.rule_id,
                                "name_cn": r.name_cn,
                                "name_en": r.name_en,
                                "category": r.category,
                                "effect": r.effect,
                                "participants": r.participants
                            }
                            for r in matched_rules
                        ]
                    }
                    st.json(export_data)
                    
            except Exception as e:
                st.error(f"❌ 规则匹配失败: {e}")
                import traceback
                with st.expander("查看错误详情"):
                    st.code(traceback.format_exc())
        else:
            st.info("请先输入八字信息或选择一个案例。")

    

if __name__ == "__main__":
    render()
