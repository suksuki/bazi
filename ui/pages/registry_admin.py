"""
🎛️ 量子注册表指挥中心
===================================
量子通用框架 (QGA) 统一管理控制台。
提供所有已注册模块、格局和系统组件的集中视图。

MVC: View Layer (Streamlit UI)
Controller: controllers/registry_management_controller.py
"""

import streamlit as st
import pandas as pd
import json


def render():
    """Entry point when loaded via main.py navigation."""
    from controllers.registry_management_controller import RegistryManagementController
    
    # ==================== PREMIUM CSS DESIGN SYSTEM ====================
    st.markdown("""
    <style>
        /* === Theme Variables === */
        :root {
            --primary: #00D9FF;
            --secondary: #7B61FF;
            --accent: #FF6B9D;
            --success: #00E676;
            --warning: #FFD600;
            --danger: #FF5252;
            --bg-dark: #0D1117;
            --bg-card: #161B22;
            --bg-hover: #21262D;
            --text-primary: #F0F6FC;
            --text-secondary: #8B949E;
            --border: #30363D;
            --glow-primary: rgba(0, 217, 255, 0.3);
            --glow-secondary: rgba(123, 97, 255, 0.3);
        }
        
        /* === Global Reset === */
        .main {
            background: linear-gradient(135deg, var(--bg-dark) 0%, #1A1F2E 100%);
        }
        
        /* === Header Section === */
        .registry-header {
            background: linear-gradient(90deg, rgba(0,217,255,0.1) 0%, rgba(123,97,255,0.1) 100%);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px 32px;
            margin-bottom: 24px;
            backdrop-filter: blur(10px);
        }
        
        .registry-title {
            font-size: 32px;
            font-weight: 700;
            background: linear-gradient(90deg, var(--primary) 0%, var(--secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }
        
        .registry-subtitle {
            color: var(--text-secondary);
            font-size: 14px;
            font-weight: 400;
        }
        
        /* === Metric Cards === */
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        
        .metric-card {
            background: linear-gradient(145deg, var(--bg-card) 0%, #1E242C 100%);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--primary) 0%, var(--secondary) 100%);
        }
        
        .metric-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 32px var(--glow-primary);
            border-color: var(--primary);
        }
        
        .metric-icon {
            font-size: 28px;
            margin-bottom: 12px;
        }
        
        .metric-value {
            font-size: 28px;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 4px;
        }
        
        .metric-label {
            font-size: 12px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* === Tab Styling === */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: var(--bg-card);
            padding: 8px;
            border-radius: 12px;
            border: 1px solid var(--border);
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 12px 20px;
            font-weight: 500;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(90deg, var(--primary) 0%, var(--secondary) 100%);
        }
        
        /* === Data Table === */
        .stDataFrame {
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--border);
        }
        
        /* === Category Badge === */
        .category-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .badge-power { background: rgba(255, 82, 82, 0.2); color: #FF5252; border: 1px solid rgba(255, 82, 82, 0.3); }
        .badge-wealth { background: rgba(255, 214, 0, 0.2); color: #FFD600; border: 1px solid rgba(255, 214, 0, 0.3); }
        .badge-flow { background: rgba(0, 217, 255, 0.2); color: #00D9FF; border: 1px solid rgba(0, 217, 255, 0.3); }
        .badge-temporal { background: rgba(123, 97, 255, 0.2); color: #7B61FF; border: 1px solid rgba(123, 97, 255, 0.3); }
        .badge-structural { background: rgba(0, 230, 118, 0.2); color: #00E676; border: 1px solid rgba(0, 230, 118, 0.3); }
        
        /* === Inspector Panel === */
        .inspector-panel {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            margin-top: 16px;
        }
        
        .inspector-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border);
        }
        
        .inspector-title {
            font-size: 18px;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        /* === Status Indicators === */
        .status-active {
            color: var(--success);
            font-weight: 600;
        }
        
        .status-inactive {
            color: var(--text-secondary);
        }
        
        .status-warning {
            color: var(--warning);
        }
        
        /* === Theme Cards === */
        .theme-card {
            background: linear-gradient(145deg, var(--bg-card) 0%, #1E242C 100%);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 12px;
            transition: all 0.3s ease;
        }
        
        .theme-card:hover {
            border-color: var(--primary);
            box-shadow: 0 4px 24px var(--glow-primary);
        }
        
        .theme-name {
            font-size: 16px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 4px;
        }
        
        .theme-desc {
            font-size: 13px;
            color: var(--text-secondary);
        }
        
        /* === Footer === */
        .footer {
            text-align: center;
            padding: 24px;
            color: var(--text-secondary);
            font-size: 12px;
            border-top: 1px solid var(--border);
            margin-top: 32px;
        }
    </style>
    """, unsafe_allow_html=True)

    # ==================== CONTROLLER INITIALIZATION ====================
    # ==================== CONTROLLER INITIALIZATION ====================
    # Updated: Force cache refresh for FDS-V3.0 upgrade
    @st.cache_resource
    def get_controller(run_id=112):
        return RegistryManagementController()

    controller = get_controller(run_id=112)

    # ==================== HEADER SECTION ====================
    st.markdown("""
    <div class="registry-header">
        <div class="registry-title">🎛️ 量子注册表指挥中心</div>
        <div class="registry-subtitle">量子通用框架 (QGA) — 系统管理控制台 | V17.1.0</div>
    </div>
    """, unsafe_allow_html=True)

    # ==================== OVERVIEW METRICS ====================
    overview = controller.get_system_overview()
    themes = controller.get_themes()

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🔢</div>
            <div class="metric-value">{overview['system_version']}</div>
            <div class="metric-label">系统版本</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🧬</div>
            <div class="metric-value">{overview['active_modules']} / {overview['total_modules']}</div>
            <div class="metric-label">活跃模块</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🌌</div>
            <div class="metric-value">{overview['active_patterns']} / {overview['total_patterns']}</div>
            <div class="metric-label">全息格局</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🎨</div>
            <div class="metric-value">{len(themes)}</div>
            <div class="metric-label">注册主题</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">📅</div>
            <div class="metric-value" style="font-size: 18px; line-height: 36px;">{overview['update_date']}</div>
            <div class="metric-label">最后更新</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ==================== MAIN TABS ====================
    tab_manifest, tab_patterns, tab_themes, tab_audit = st.tabs([
        "🧬 逻辑总线 (MODs)",
        "🌌 全息格局注册表",
        "🎨 主题注册表",
        "🔎 合规审计"
    ])

    # === Tab 1: Logic Manifest ===
    with tab_manifest:
        st.markdown("### 系统模块 (逻辑总线)")
        
        # Toolbar
        col_search, col_filter, col_layer = st.columns([2, 1, 1])
        with col_search:
            search_term = st.text_input("🔍 搜索模块", placeholder="例如: MOD_15, Wealth, Temporal...", label_visibility="collapsed")
        with col_filter:
            status_filter = st.selectbox("状态", ["全部", "活跃", "禁用"], label_visibility="collapsed")
        with col_layer:
            all_layers = controller.get_all_layers()
            layer_filter = st.selectbox("层级", ["全部"] + all_layers, label_visibility="collapsed")
        
        # Data Table
        modules_data = controller.get_modules_dataframe_data()
        df_modules = pd.DataFrame(modules_data)
        
        # Apply filters
        if search_term:
            df_modules = df_modules[
                df_modules['Name'].str.contains(search_term, case=False) | 
                df_modules['ID'].str.contains(search_term, case=False) |
                df_modules['Description'].str.contains(search_term, case=False)
            ]
        
        if status_filter == "活跃":
            df_modules = df_modules[df_modules['Status'].str.contains("✅")]
        elif status_filter == "禁用":
            df_modules = df_modules[df_modules['Status'].str.contains("⛔")]
        
        if layer_filter != "全部":
            df_modules = df_modules[df_modules['Layer'] == layer_filter]
        
        st.dataframe(
            df_modules,
            use_container_width=True,
            column_config={
                "Icon": st.column_config.TextColumn("", width="small"),
                "ID": st.column_config.TextColumn("模块ID", width="medium"),
                "Name": st.column_config.TextColumn("模块名称", width="large"),
                "Layer": st.column_config.TextColumn("层级", width="medium"),
                "Status": st.column_config.TextColumn("状态", width="small"),
                "Theme": st.column_config.TextColumn("主题", width="medium"),
                "Description": st.column_config.TextColumn("描述", width="large"),
            },
            hide_index=True,
            height=400
        )
        
        # Module Inspector
        st.markdown("### 🔬 模块检视器")
        col_select, col_info = st.columns([1, 2])
        
        with col_select:
            if not df_modules.empty:
                selected_mod_id = st.selectbox(
                    "选择要检视的模块",
                    options=df_modules['ID'].tolist(),
                    format_func=lambda x: f"{x}"
                )
            else:
                selected_mod_id = None
                st.info("没有模块符合您的筛选条件")
        
        with col_info:
            if selected_mod_id:
                details = controller.get_module_details(selected_mod_id)
                if details:
                    st.markdown(f"""
                    **层级:** `{details.get('layer', 'N/A')}`  
                    **优先级:** `{details.get('priority', 'N/A')}`  
                    **状态:** `{details.get('status', 'N/A')}`  
                    **主题:** `{details.get('theme', 'N/A')}`
                    """)
        
        if selected_mod_id:
            with st.expander("📄 原始 JSON 定义", expanded=False):
                details = controller.get_module_details(selected_mod_id)
                st.json(details)

    # === Tab 2: Holographic Patterns ===
    with tab_patterns:
        st.markdown("### 格局注册表 (全息系列)")
        
        patterns_data = controller.get_patterns_dataframe_data()
        df_patterns_tab2 = pd.DataFrame(patterns_data)
        
        # Filter toolbar
        col_cat, col_status = st.columns([1, 1])
        with col_cat:
            all_categories = df_patterns_tab2['Category'].unique().tolist() if not df_patterns_tab2.empty else []
            cat_filter = st.selectbox("类别", ["全部"] + all_categories, key="pat_cat", label_visibility="collapsed")
        with col_status:
            pat_status = st.selectbox("状态", ["全部", "合规 ✅", "不合规 ⚠️"], key="pat_status", label_visibility="collapsed")
        
        # Apply filters
        df_patterns_filtered = df_patterns_tab2.copy()
        if cat_filter != "全部":
            df_patterns_filtered = df_patterns_filtered[df_patterns_filtered['Category'] == cat_filter]
        if pat_status == "合规 ✅":
            # Show V3.0 compliant patterns (must contain both ✅ and "最新标准")
            mask = (df_patterns_filtered['Compliance'].str.contains("✅", na=False)) & \
                   (df_patterns_filtered['Compliance'].str.contains("最新标准", na=False))
            df_patterns_filtered = df_patterns_filtered[mask]
        elif pat_status == "不合规 ⚠️":
            # Show deprecated or non-compliant patterns
            mask = (df_patterns_filtered['Compliance'].str.contains("已废弃", na=False)) | \
                   (df_patterns_filtered['Compliance'].str.contains("不合规", na=False))
            df_patterns_filtered = df_patterns_filtered[mask]
        
        st.dataframe(
            df_patterns_filtered,
            use_container_width=True,
            column_config={
                "ID": st.column_config.TextColumn("格局 ID", width="small"),
                "Name": st.column_config.TextColumn("名称", width="large"),
                "CN Name": st.column_config.TextColumn("中文名", width="medium"),
                "Category": st.column_config.TextColumn("类别", width="small"),
                "Compliance": st.column_config.TextColumn("标准", width="medium"),
                "Version": st.column_config.TextColumn("版本", width="small"),
                "Sub-Patterns": st.column_config.ProgressColumn("子格局", min_value=0, max_value=10, format="%d"),
            },
            hide_index=True,
            height=300
        )
        
        # Pattern Inspector with split view
        st.markdown("### 🔬 格局检视器")
        
        if not df_patterns_filtered.empty:
            selected_pat_id = st.selectbox(
                "选择要检视的格局",
                options=df_patterns_filtered['ID'].tolist()
            )
            
            if selected_pat_id:
                pat_details = controller.get_pattern_details(selected_pat_id)
                
                col_main, col_subs = st.columns([1, 1])
                
                with col_main:
                    st.markdown("#### 📋 格局定义")
                    
                    meta = pat_details.get('meta_info', {})
                    physics = pat_details.get('physics_kernel', {})
                    
                    st.markdown(f"""
                    **名称:** {pat_details.get('name', 'N/A')}  
                    **中文:** {pat_details.get('name_cn', 'N/A')}  
                    **类别:** `{pat_details.get('category', 'N/A')}`  
                    **版本:** `{pat_details.get('version', 'N/A')}`  
                    **合规性:** `{meta.get('compliance', 'N/A')}`  
                    **物理原型:** {meta.get('physics_prototype', 'N/A')}
                    """)
                    
                    if physics:
                        with st.expander("🧪 物理内核", expanded=False):
                            st.json(physics)
                    
                    router = pat_details.get('matching_router', {})
                    if router:
                        with st.expander("🔀 匹配路由器", expanded=False):
                            st.json(router)
                
                with col_subs:
                    st.markdown("#### 📁 子格局注册表")
                    subs = pat_details.get('sub_patterns_registry', [])
                    
                    if subs:
                        for sp in subs:
                            risk = sp.get('risk_level', 'NORMAL')
                            risk_color = {
                                'HIGH': '🔴',
                                'MEDIUM': '🟡',
                                'LOW': '🟢',
                                'NORMAL': '⚪'
                            }.get(risk, '⚪')
                            
                            with st.expander(f"{risk_color} **{sp.get('id')}** - {sp.get('name', 'N/A')}", expanded=False):
                                st.markdown(f"**风险等级:** `{risk}`")
                                st.markdown(f"**描述:** {sp.get('description', 'N/A')}")
                                
                                manifold = sp.get('manifold_data', {})
                                if manifold:
                                    st.markdown("**均值向量:**")
                                    st.json(manifold.get('mean_vector', {}))
                    else:
                        st.info("此格局没有已注册的子格局")
        else:
            st.info("没有格局符合您的筛选条件")

    # === Tab 3: Theme Registry ===
    with tab_themes:
        st.markdown("### 已注册主题")
        st.markdown("主题用于在量子通用框架中组织和分类模块与格局。")
        
        for theme_id, theme_info in themes.items():
            with st.container():
                st.markdown(f"""
                <div class="theme-card">
                    <div class="theme-name">{theme_info.get('name', theme_id)}</div>
                    <div class="theme-desc">{theme_info.get('description', '暂无描述')}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Show modules in this theme
                theme_modules = controller.get_modules_by_theme(theme_id)
                if theme_modules:
                    with st.expander(f"📦 此主题下 {len(theme_modules)} 个模块"):
                        for mod in theme_modules:
                            status_icon = "✅" if mod.get('active', False) else "⛔"
                            st.markdown(f"{status_icon} **{mod.get('id')}**: {mod.get('name', 'N/A')}")
                
                # Show patterns in this theme (for HOLOGRAPHIC_PATTERN)
                theme_patterns = controller.get_patterns_by_theme(theme_id)
                if theme_patterns:
                    with st.expander(f"🌌 此主题下 {len(theme_patterns)} 个格局"):
                        for pat in theme_patterns:
                            status_icon = "✅" if pat.get('active', False) else "⛔"
                            icon = pat.get('icon', '🌌')
                            st.markdown(f"{status_icon} {icon} **{pat.get('id')}**: {pat.get('name_cn', pat.get('name', 'N/A'))} ({pat.get('category', '')})")

    # === Tab 4: Compliance Audit ===
    with tab_audit:
        st.markdown("### FDS-V3.0 合规报告")
        
        col_status, col_action = st.columns([3, 1])
        
        with col_status:
            # Re-fetch patterns data for audit tab (don't use filtered data from tab 2)
            patterns_data_audit = controller.get_patterns_dataframe_data()
            df_patterns_audit = pd.DataFrame(patterns_data_audit)
            
            if not df_patterns_audit.empty:
                # Non-compliant = not V3.0 (doesn't contain "最新标准")
                non_compliant = df_patterns_audit[~df_patterns_audit['Compliance'].str.contains("最新标准", na=False)]
                
                if not non_compliant.empty:
                    st.error(f"⚠️ 发现 **{len(non_compliant)}** 个不符合 FDS-V3.0 标准的格局！")
                    st.dataframe(
                        non_compliant[['ID', 'Name', 'Compliance', 'Version']],
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Count V3.0 compliant
                    v3_compliant = df_patterns_audit[df_patterns_audit['Compliance'].str.contains("最新标准", na=False)]
                    st.info(f"✅ **{len(v3_compliant)}** 个格局已升级到 FDS-V3.0 标准")
                else:
                    st.success("✅ 所有已注册格局均 **符合 FDS-V3.0 标准**！")
            else:
                st.info("暂无已注册的格局数据")
        
        with col_action:
            if st.button("♻️ 刷新注册表", use_container_width=True):
                controller.refresh_data()
                st.cache_resource.clear()
                st.rerun()
        
        st.markdown("---")
        
        # Compliance Standards Reference
        st.markdown("#### 📜 合规标准参考")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **格局要求 (FDS-V3.0)**
            - ✅ 必须定义 `physics_kernel` 包含 `transfer_matrix`
            - ✅ 必须定义 `meta_info.compliance: "FDS-V3.0"`
            - ✅ 必须使用 `@config.xxx` 配置引用（零硬编码）
            - ✅ 必须定义 `matching_router` 使用 `param_ref` 而非 `value`
            - ✅ 必须定义 `integrity_threshold_ref` 和 `k_factor_ref`
            - ✅ 如适用应定义 `sub_patterns_registry`
            """)
        
        with col2:
            st.markdown("""
            **模块要求 (QGA V17.x)**
            - ✅ 必须定义 `layer` 用于物理集成
            - ✅ 必须定义 `linked_rules` 和 `linked_metrics`
            - ✅ 核心模块必须设为 `active: true`
            - ✅ 必须属于已注册的 `theme`
            """)
        
        # System Health Check
        st.markdown("---")
        st.markdown("#### 🩺 系统健康检查")
        
        health_metrics = controller.get_system_health()
        
        hcol1, hcol2, hcol3, hcol4 = st.columns(4)
        
        with hcol1:
            st.metric(
                "模块覆盖率",
                f"{health_metrics['module_coverage']:.1%}",
                help="活跃模块百分比"
            )
        
        with hcol2:
            st.metric(
                "格局覆盖率",
                f"{health_metrics['pattern_coverage']:.1%}",
                help="活跃格局百分比"
            )
        
        with hcol3:
            st.metric(
                "主题利用率",
                f"{health_metrics['theme_utilization']:.1%}",
                help="有活跃模块的主题百分比"
            )
        
        with hcol4:
            st.metric(
                "合规率",
                f"{health_metrics['compliance_rate']:.1%}",
                help="FDS合规格局百分比"
            )

    # ==================== FOOTER ====================
    st.markdown("""
    <div class="footer">
        量子通用框架 | 注册表管理控制台 | V17.1.0<br>
        <span style="color: #00D9FF;">🧬 ANTIGRAVITY_CORE_ALPHA</span>
    </div>
    """, unsafe_allow_html=True)
