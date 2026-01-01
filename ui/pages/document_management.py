#!/usr/bin/env python3
"""
规范文档管理页面 (Document Management Page)
MVC View Layer - 只负责UI展示，所有业务逻辑通过Controller处理
"""

import streamlit as st
import sys
import re
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# MVC: 只导入Controller，不直接操作Model
from controllers.document_management_controller import DocumentManagementController
from ui.components.theme import apply_custom_header, sidebar_header

# 全局Controller缓存函数
@st.cache_resource(ttl=0, max_entries=1)
def get_controller():
    """获取文档管理控制器（带缓存）"""
    return DocumentManagementController()

def render():
    """渲染规范文档管理页面 (Unified Quantum Workspace)"""
    st.set_page_config(
        page_title="规范文档管理",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # ==================== PREMIUM CSS DESIGN SYSTEM ====================
    st.markdown("""
    <style>
        :root {
            --primary: #00D9FF;
            --secondary: #7B61FF;
            --accent: #FF6B9D;
            --success: #00E676;
            --warning: #FFD600;
            --danger: #FF5252;
            --bg-dark: #0D1117;
            --bg-card: rgba(22, 27, 34, 0.7);
            --bg-hover: rgba(33, 38, 45, 0.9);
            --text-primary: #F0F6FC;
            --text-secondary: #8B949E;
            --border: #30363D;
            --glow-primary: rgba(0, 217, 255, 0.3);
        }
        
        .doc-metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        
        .doc-metric-card {
            background: linear-gradient(145deg, rgba(22, 27, 34, 0.8) 0%, rgba(30, 36, 44, 0.8) 100%);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }
        
        .doc-metric-card:hover {
            transform: translateY(-4px);
            border-color: var(--primary);
            box-shadow: 0 8px 24px var(--glow-primary);
        }
        
        .doc-metric-value { font-size: 24px; font-weight: 700; color: var(--primary); }
        .doc-metric-label { font-size: 11px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 1px; }
        
        .doc-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        .doc-card:hover {
            background: var(--bg-hover);
            border-color: var(--primary);
            box-shadow: 0 4px 20px rgba(0, 217, 255, 0.1);
        }
        
        .doc-title { font-size: 1.2rem; font-weight: 600; color: var(--text-primary); margin-bottom: 8px; display: flex; align-items: center; gap: 10px; }
        .doc-meta { display: flex; gap: 15px; font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 15px; }
        
        .badge { padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 500; border: 1px solid rgba(255, 255, 255, 0.1); }
        .badge-category { background: rgba(123, 97, 255, 0.1); color: #7B61FF; }
        .badge-version { background: rgba(0, 217, 255, 0.1); color: #00D9FF; }
        .badge-deprecated { background: rgba(255, 82, 82, 0.1); color: #FF5252; border-color: rgba(255, 82, 82, 0.2); }
        
        /* Monospaced Editor & Preview Alignment */
        div[data-testid="stTextArea"] textarea, .doc-content-box {
            font-family: var(--font-mono) !important;
            font-size: 0.9rem !important;
            line-height: 1.6 !important;
            background: rgba(255, 255, 255, 0.02) !important;
            color: var(--text-primary) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 8px !important;
            padding: 20px !important;
            transition: all 0.2s ease;
        }
        
        div[data-testid="stTextArea"] textarea:focus {
            border-color: var(--primary) !important;
            background: rgba(255, 255, 255, 0.05) !important;
            outline: none !important;
        }

        /* Unified Action Buttons */
        div[data-testid="stButton"] button {
            border-radius: 6px !important;
            padding: 4px 12px !important;
            height: 34px !important;
            font-size: 0.8rem !important;
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: var(--text-secondary) !important;
            transition: all 0.2s ease !important;
            width: 100% !important;
            font-family: var(--font-main) !important;
        }
        
        div[data-testid="stButton"] button:hover {
            border-color: var(--primary) !important;
            color: var(--primary) !important;
            background: rgba(0, 217, 255, 0.04) !important;
            box-shadow: 0 2px 8px rgba(0, 217, 255, 0.1) !important;
        }

        /* Strong Selection Highlight for Editor */
        textarea::selection {
            background: #00E676 !important;
            color: #000000 !important;
        }
        textarea::-moz-selection {
            background: #00E676 !important;
            color: #000000 !important;
        }

        .doc-preview-box {
            height: 500px;
            overflow-y: auto;
            scrollbar-width: thin;
            scrollbar-color: var(--border) transparent;
        }

        /* Holographic Config Links Enhancement */
        .cfg-link {
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            display: inline-block;
        }
        .cfg-link:hover {
            transform: scale(1.05);
            filter: drop-shadow(0 0 8px rgba(0, 230, 118, 0.4));
        }
    </style>
    """, unsafe_allow_html=True)

    # 页面标题
    apply_custom_header("📚 规范文档管理", "Quantum Specification & Compliance Center | V3.0")
    
    # --- Query Param Router (Smart Navigation) ---
    q_params = st.query_params
    should_rerun = False
    
    if "anchor_cfg" in q_params:
        st.session_state['active_anchor_cfg'] = q_params["anchor_cfg"]
        st.session_state['config_center_active'] = True
        st.session_state['selected_document'] = None
        should_rerun = True
    elif "selected_doc" in q_params:
        target_doc = q_params["selected_doc"]
        if target_doc != st.session_state.get('selected_document'):
            st.session_state['selected_document'] = target_doc
            st.session_state['config_center_active'] = False # 切换回文档模式
            should_rerun = True

    if should_rerun:
        st.query_params.clear()
        st.rerun()

    # MVC: 初始化Controller
    controller = get_controller()
    
    # 侧边栏：文档分类导航
    with st.sidebar:
        sidebar_header("📖 文档索引")
        
        categories = controller.get_categories()
        all_categories = ["全部"] + categories
        
        selected_category = st.radio("选择分类", all_categories, index=0, label_visibility="collapsed")
        
        if st.button("🔄 刷新系统总线", use_container_width=True):
            get_controller.clear()
            st.rerun()
            
        st.markdown('<div style="margin: 15px 0; border-bottom: 1px solid rgba(255,255,255,0.1);"></div>', unsafe_allow_html=True)
        if st.button("⚙️ 全息配置中心", use_container_width=True):
            st.session_state['config_center_active'] = not st.session_state.get('config_center_active', False)
            st.session_state['selected_document'] = None # 进入配置中心时取消文档选择
            st.rerun()

    # 处理状态切换
    if st.session_state.get('config_center_active', False):
        _render_config_center()
    else:
        selected_doc = st.session_state.get('selected_document')
        if selected_doc:
            # 详细工作空间视图
            _render_unified_workspace(controller, selected_doc)
        else:
            # 全息规约矩阵视图 (列表)
            summary = controller.get_documents_summary()
            total_docs = len(controller.get_documents_by_category(None, include_deprecated=True))
            active_docs = len(controller.get_documents_by_category(None, include_deprecated=False))
            deprecated_docs = total_docs - active_docs
            
            # 显示列表页特有的 Metrics
            st.markdown(f"""
            <div class="doc-metric-grid">
                <div class="doc-metric-card">
                    <div class="doc-metric-value">{total_docs}</div>
                    <div class="doc-metric-label">所有规约</div>
                </div>
                <div class="doc-metric-card">
                    <div class="doc-metric-value">{active_docs}</div>
                    <div class="doc-metric-label">活跃标准</div>
                </div>
                <div class="doc-metric-card">
                    <div class="doc-metric-value">{deprecated_docs}</div>
                    <div class="doc-metric-label">已归档</div>
                </div>
                <div class="doc-metric-card">
                    <div class="doc-metric-value">{len(summary['categories'])}</div>
                    <div class="doc-metric-label">分类矩阵</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            _render_document_list(controller, selected_category)


def _render_config_center():
    """渲染全息配置中心 - 增强精准定位版"""
    import os
    import json
    import streamlit.components.v1 as components
    from urllib.parse import quote
    from pathlib import Path
    
    apply_custom_header("⚙️ 全息配置中心", "Holographic System Manifest & Logic Config | Master Control")
    
    # --- 1. 文件路由 ---
    anchor = st.session_state.get('active_anchor_cfg')
    project_root = Path(__file__).parent.parent.parent
    
    # 配置文件路径（使用绝对路径）
    config_json_path = project_root / "core" / "config.json"
    manifest_json_path = project_root / "core" / "logic_manifest.json"
    
    # 默认显示 config.json（这是正确的配置文件，包含所有 @config.* 引用的参数）
    # 【首次初始化】如果不存在，从 core/config.py 导出（仅此一次，之后文件持久化存在）
    if not config_json_path.exists():
        try:
            # 从 core/config.py 导出配置（仅首次初始化）
            from core.config import config
            import json
            
            config_dict = {
                'version': config.version,
                'gating': {
                    'min_self_energy': config.gating.min_self_energy,
                    'weak_self_limit': config.gating.weak_self_limit,
                    'max_relation': config.gating.max_relation,
                    'max_relation_limit': config.gating.max_relation_limit,
                    'min_wealth_level': config.gating.min_wealth_level
                },
                'physics': {
                    'k_factor': config.physics.k_factor,
                    'precision_weights': {
                        'similarity': config.physics.precision_weights.similarity,
                        'distance': config.physics.precision_weights.distance
                    },
                    'precision_gaussian_sigma': config.physics.precision_gaussian_sigma,
                    'precision_energy_gate_k': config.physics.precision_energy_gate_k,
                    'rooting_weights': config.physics.rooting_weights,
                    'projection_bonus': config.physics.projection_bonus,
                    'spatial_decay': config.physics.spatial_decay,
                    'global_entropy': config.physics.global_entropy
                },
                'spacetime': {
                    'macro_bonus': config.spacetime.macro_bonus,
                    'latitude_coefficients': config.spacetime.latitude_coefficients,
                    'invert_seasons': config.spacetime.invert_seasons,
                    'solar_time_correction': config.spacetime.solar_time_correction
                },
                'vault': {
                    'threshold': config.vault.threshold,
                    'sealed_damping': config.vault.sealed_damping,
                    'open_bonus': config.vault.open_bonus,
                    'collapse_penalty': config.vault.collapse_penalty
                },
                'flow': {
                    'generation_efficiency': config.flow.generation_efficiency,
                    'control_impact': config.flow.control_impact
                },
                'interactions': {
                    'clash_damping': config.interactions.clash_damping
                },
                'mediation': {
                    'threshold': config.mediation.threshold
                },
                'singularity': {
                    'threshold': config.singularity.threshold,
                    'distance_threshold': config.singularity.distance_threshold,
                    'min_samples': config.singularity.min_samples,
                    'clustering_min_samples': config.singularity.clustering_min_samples
                },
                'clustering': {
                    'min_samples': config.clustering.min_samples
                },
                'patterns': {
                    'a03': config.patterns.a03,
                    'd01': config.patterns.d01,
                    'd02': config.patterns.d02,
                    'b01': config.patterns.b01,
                    'a01': config.patterns.a01,
                    'b02': config.patterns.b02
                }
            }
            
            with open(config_json_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            st.success(f"✅ **首次初始化**: 已从 `core/config.py` 导出配置到 `{config_json_path.name}`")
            st.info("💡 **说明**: 文件已创建，之后会持久化保存。您的修改不会丢失。")
        except Exception as e:
            st.error(f"无法导出 config.json: {e}")
            # 如果导出失败，使用 logic_manifest.json 作为备选
            if manifest_json_path.exists():
                target_file = str(manifest_json_path)
            else:
                st.error("没有可用的配置文件")
                return
    
    # 默认使用 config.json
    target_file = str(config_json_path)

    # 面包屑
    st.markdown(f"**路径**: `System` > `{os.path.basename(target_file)}`" + (f" > `🎯 {anchor}`" if anchor else ""))
    
    # 读取文件内容
    try:
        if not os.path.exists(target_file):
            # 如果文件不存在，尝试创建默认的 config.json
            if target_file.endswith('config.json'):
                st.warning(f"⚠️ 文件 `{os.path.basename(target_file)}` 不存在，正在创建默认配置...")
                default_config = {
                    "version": "3.0",
                    "description": "Antigravity V3.0 Configuration",
                    "config": {}
                }
                with open(target_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)
                raw_data = json.dumps(default_config, indent=2, ensure_ascii=False)
                json_data = default_config
                st.success(f"✅ 已创建默认配置文件: {os.path.basename(target_file)}")
            else:
                st.error(f"配置文件不存在: {target_file}")
                return
        else:
            with open(target_file, 'r', encoding='utf-8') as f:
                raw_data = f.read()
                json_data = json.loads(raw_data)
    except json.JSONDecodeError as je:
        st.error(f"JSON 解析错误: {je}")
        return
    except Exception as e:
        st.error(f"无法读取配置文件 {target_file}: {e}")
        return

    # 返回按钮与锚点清除
    col_nav, col_action = st.columns([1, 4])
    with col_nav:
        if st.button("⬅️ 返回矩阵", use_container_width=True):
            st.session_state['config_center_active'] = False
            st.session_state['active_anchor_cfg'] = None
            st.rerun()
            
    with col_action:
        # --- 2. 深度锚定高亮 Spotlight ---
        if anchor:
            last_key = anchor.split('.')[-1]
            lines = raw_data.split('\n')
            found_line = -1
            for i, line in enumerate(lines):
                # JSON 格式匹配
                if f'"{last_key}"' in line or f'{last_key}:' in line:
                    found_line = i + 1
                    break
            
            st.markdown(f"""
            <div style="background: rgba(0, 230, 118, 0.08); border: 1px solid rgba(0, 230, 118, 0.4); border-radius: 8px; padding: 12px; border-left: 5px solid #00E676; margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: #00E676; font-size: 0.75rem; font-weight: bold; text-transform: uppercase;">Acyclic Anchor Locked</span>
                        <div style="font-size: 1.1rem; color: #F0F6FC; font-family: monospace; margin-top: 2px;">@{anchor}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: #8B949E; font-size: 0.75rem;">定位行号</div>
                        <div style="font-size: 1.2rem; color: #00E676; font-weight: bold;">L-{found_line if found_line > 0 else "???"}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 源代码切片预览 (Spotlight)
            if found_line > 0:
                start_l = max(0, found_line - 3)
                end_l = min(len(lines), found_line + 2)
                snippet = "\n".join(lines[start_l:end_l])
                st.code(snippet, language="json", line_numbers=True)
                
            if st.button("❌ 释放锚定聚焦", use_container_width=False):
                st.session_state['active_anchor_cfg'] = None
                st.rerun()

    st.markdown('<div style="margin-bottom: 20px;"></div>', unsafe_allow_html=True)
    
    # --- 3. 文件状态提示 ---
    if target_file.endswith('config.json'):
        col_info, col_sync = st.columns([3, 1])
        with col_info:
            if config_json_path.exists():
                file_mtime = os.path.getmtime(config_json_path)
                from datetime import datetime
                mtime_str = datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d %H:%M:%S')
                st.caption(f"📄 **文件状态**: 已持久化 | 最后修改: {mtime_str}")
            else:
                st.caption("📄 **文件状态**: 首次初始化中...")
        with col_sync:
            if config_json_path.exists() and target_file.endswith('config.json'):
                if st.button("🔄 从 config.py 同步", help="⚠️ 警告：会覆盖当前 JSON 中的所有修改！", use_container_width=True):
                    st.session_state['show_sync_confirm'] = True
                    st.rerun()
        
        # 同步确认对话框
        if st.session_state.get('show_sync_confirm', False):
            st.warning("⚠️ **确认同步**: 这将用 `core/config.py` 的默认值覆盖 `config.json` 的所有内容！您的修改将丢失。")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("✅ 确认覆盖", type="primary", use_container_width=True):
                    try:
                        from core.config import config
                        # 重新导出配置（与初始化逻辑相同）
                        config_dict = {
                            'version': config.version,
                            'gating': {
                                'min_self_energy': config.gating.min_self_energy,
                                'weak_self_limit': config.gating.weak_self_limit,
                                'max_relation': config.gating.max_relation,
                                'max_relation_limit': config.gating.max_relation_limit,
                                'min_wealth_level': config.gating.min_wealth_level
                            },
                            'physics': {
                                'k_factor': config.physics.k_factor,
                                'precision_weights': {
                                    'similarity': config.physics.precision_weights.similarity,
                                    'distance': config.physics.precision_weights.distance
                                },
                                'precision_gaussian_sigma': config.physics.precision_gaussian_sigma,
                                'precision_energy_gate_k': config.physics.precision_energy_gate_k,
                                'rooting_weights': config.physics.rooting_weights,
                                'projection_bonus': config.physics.projection_bonus,
                                'spatial_decay': config.physics.spatial_decay,
                                'global_entropy': config.physics.global_entropy
                            },
                            'spacetime': {
                                'macro_bonus': config.spacetime.macro_bonus,
                                'latitude_coefficients': config.spacetime.latitude_coefficients,
                                'invert_seasons': config.spacetime.invert_seasons,
                                'solar_time_correction': config.spacetime.solar_time_correction
                            },
                            'vault': {
                                'threshold': config.vault.threshold,
                                'sealed_damping': config.vault.sealed_damping,
                                'open_bonus': config.vault.open_bonus,
                                'collapse_penalty': config.vault.collapse_penalty
                            },
                            'flow': {
                                'generation_efficiency': config.flow.generation_efficiency,
                                'control_impact': config.flow.control_impact
                            },
                            'interactions': {
                                'clash_damping': config.interactions.clash_damping
                            },
                            'mediation': {
                                'threshold': config.mediation.threshold
                            },
                            'singularity': {
                                'threshold': config.singularity.threshold,
                                'distance_threshold': config.singularity.distance_threshold,
                                'min_samples': config.singularity.min_samples,
                                'clustering_min_samples': config.singularity.clustering_min_samples
                            },
                            'clustering': {
                                'min_samples': config.clustering.min_samples
                            },
                            'patterns': {
                                'a03': config.patterns.a03,
                                'd01': config.patterns.d01,
                                'd02': config.patterns.d02,
                                'b01': config.patterns.b01,
                                'a01': config.patterns.a01,
                                'b02': config.patterns.b02
                            }
                        }
                        with open(config_json_path, 'w', encoding='utf-8') as f:
                            json.dump(config_dict, f, indent=2, ensure_ascii=False)
                        st.session_state['show_sync_confirm'] = False
                        st.success("✅ 已从 `core/config.py` 同步配置（已覆盖）")
                        st.rerun()
                    except Exception as e:
                        st.error(f"同步失败: {e}")
            with col_no:
                if st.button("❌ 取消", use_container_width=True):
                    st.session_state['show_sync_confirm'] = False
                    st.rerun()
    
    # --- 4. 增强型全息源码编辑器 ---
    st.markdown(f"#### ✍️ 源码编辑: `{os.path.basename(target_file)}`" + (" (已自动定位目标字段)" if anchor else ""))
    
    # 注入 JS 自动滚轴脚本 (如果存在锚点)
    if anchor and found_line > 0:
        target_text = f'"{last_key}"'
        js_code = f"""
            <script>
            function performHolographicScroll() {{
                const textareas = window.parent.document.querySelectorAll('textarea');
                const targetStr = '{target_text}';
                for (let ta of textareas) {{
                    if (ta.value.includes(targetStr)) {{
                        const lines = ta.value.split('\\n');
                        let idx = -1;
                        for(let i=0; i<lines.length; i++) {{
                            if(lines[i].includes(targetStr)) {{ idx = i; break; }}
                        }}
                            if(idx !== -1) {{
                                const scrollPos = idx * 24; 
                                ta.scrollTop = scrollPos - 150;
                                
                                // 强制执行高亮选中
                                const start = ta.value.indexOf(targetStr);
                                if (start !== -1) {{
                                    ta.focus();
                                    ta.setSelectionRange(start, start + targetStr.length);
                                    
                                    // 模拟闪烁效果 (通过暂时改变背景或边框，如果不支持，则通过多次选中)
                                    ta.style.borderColor = "#00E676";
                                    setTimeout(() => {{ ta.style.borderColor = "rgba(255, 255, 255, 0.1)"; }}, 500);
                                    setTimeout(() => {{ ta.style.borderColor = "#00E676"; }}, 1000);
                                    setTimeout(() => {{ ta.style.borderColor = "rgba(255, 255, 255, 0.1)"; }}, 1500);
                                }}
                            }}
                    }}
                }}
            }}
            // 多次尝试确保页面渲染完成
            setTimeout(performHolographicScroll, 500);
            setTimeout(performHolographicScroll, 1500);
            </script>
        """
        components.html(js_code, height=0)

    edited_code = st.text_area(
        "Source Editor",
        value=raw_data,
        height=700,
        key="config_editor_area_v2",
        label_visibility="collapsed",
        help="编辑物理参数后，点击下方同步按钮持久化到系统底层。"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("💾 物理同步", type="primary", use_container_width=True):
            try:
                # JSON 语法核验
                json.loads(edited_code)
                
                # 保存文件
                with open(target_file, 'w', encoding='utf-8') as f:
                    f.write(edited_code)
                st.success(f"✅ 「{os.path.basename(target_file)}」已完成全息同步。")
                
                # 清除相关缓存
                try:
                    get_controller.clear()
                except:
                    pass
                
                st.rerun()
            except json.JSONDecodeError as jde:
                st.error(f"❌ JSON 语法错误: {jde}")
            except Exception as ex:
                st.error(f"❌ 同步失败: {ex}")
    with col2:
        st.caption(f"💡 当前文件: {target_file} | 格式: JSON")


def _render_document_list(controller: DocumentManagementController, category: str):
    """渲染文档列表"""
    col_header, col_filter = st.columns([3, 1])
    
    with col_header:
        st.subheader("📋 规约矩阵视图")
    
    with col_filter:
        include_deprecated = st.checkbox("包含已归档文档", value=True, key="include_deprecated")
    
    # 获取文档列表
    if category == "全部":
        documents = controller.get_documents_by_category(None, include_deprecated=include_deprecated)
    else:
        documents = controller.get_documents_by_category(category, include_deprecated=include_deprecated)
    
    if not documents:
        st.info("📭 该分类下暂无文档")
        return
    
    # 分类显示
    if category == "全部":
        categories = controller.get_categories()
        for cat in categories:
            cat_docs = [doc for doc in documents if doc.category == cat]
            if not cat_docs:
                continue
            
            cat_info = controller.get_category_info(cat)
            icon = cat_info.icon if cat_info else "📄"
            
            with st.expander(f"{icon} {cat} ({len(cat_docs)})", expanded=True):
                _render_document_cards(controller, cat_docs)
    else:
        _render_document_cards(controller, documents)


def _render_document_cards(controller: DocumentManagementController, documents):
    """渲染文档卡片列表 (Premium Design)"""
    for doc in documents:
        # 使用HTML渲染卡片结构
        deprecated_tag = '<span class="badge badge-deprecated">已归档</span>' if doc.deprecated else ""
        time_str = doc.last_modified.strftime("%Y-%m-%d %H:%M") if doc.last_modified else "Unknown"
        
        st.markdown(f"""
        <div class="doc-card">
            <div class="doc-title">📄 {doc.title} {deprecated_tag}</div>
            <div class="doc-meta">
                <span class="badge badge-category">{doc.category}</span>
                <span class="badge badge-version">V{doc.version or '---'}</span>
                <span>ID: {doc.filename}</span>
                <span>🕐 {time_str}</span>
            </div>
            <div style="margin-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 10px;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        # --- Card Body: Dual-Mode Integrated Editor & Linkage ---
        doc_data = controller.read_document(doc.filename)
        if doc_data['success']:
            # 引入内嵌选项卡，解决文本框无法渲染链接的问题
            mode_tab_edit, mode_tab_link = st.tabs(["📝 源码编辑", "🔗 全息链接"])
            
            with mode_tab_edit:
                edited_text = st.text_area(
                    "规约正文", 
                    value=doc_data['content'], 
                    height=450, 
                    key=f"card_body_edit_{doc.filename}_{id(doc)}",
                    label_visibility="collapsed"
                )
            
            with mode_tab_link:
                # 渲染带链接的全息预览（包含文档引用和配置引用）
                rendered_content = _highlight_doc_refs_in_markdown(controller, doc_data['content'], doc.filename)
                rendered_content_with_config = _highlight_config_refs_in_markdown(controller, rendered_content, doc.filename)
                st.markdown(f"""
                <div class="doc-content-box doc-preview-box" style="height: 400px; overflow-y: auto;">
                    {rendered_content_with_config}
                </div>
                """, unsafe_allow_html=True)
                
                # 配置引用快捷按钮区域
                refs_info = controller.get_document_references(doc.filename)
                if refs_info['references']['config_refs']:
                    st.markdown("---")
                    st.caption("⚙️ **配置引用快捷跳转**（悬停查看值，点击跳转到配置中心定位）")
                    config_ref_cols = st.columns(min(len(refs_info['references']['config_refs']), 4))
                    for idx, config_ref in enumerate(refs_info['references']['config_refs'][:8]):  # 最多显示8个
                        config_path = config_ref.replace('@config.', '')
                        config_value = controller.resolve_config_ref_link(config_path)
                        display_value = str(config_value)[:30] + "..." if config_value and len(str(config_value)) > 30 else (str(config_value) if config_value else "未找到")
                        with config_ref_cols[idx % len(config_ref_cols)]:
                            if st.button(f"⚙️ {config_path.split('.')[-1]}", key=f"card_config_link_{config_ref}_{doc.filename}_{idx}", use_container_width=True, help=f"{config_ref} = {display_value}"):
                                # 设置锚点并跳转到配置中心
                                st.session_state['config_center_active'] = True
                                st.session_state['active_anchor_cfg'] = config_path
                                st.session_state['selected_document'] = None
                                st.rerun()
                    if len(refs_info['references']['config_refs']) > 8:
                        st.caption(f"... 还有 {len(refs_info['references']['config_refs']) - 8} 个配置引用")
            
            # --- 操作工具栏 ---
            tool_cols = st.columns([1.5, 1.5, 0.7, 0.7, 3])
            
            with tool_cols[0]:
                if st.button("💾 同步文档", key=f"save_inline_{doc.filename}", use_container_width=True):
                    save_res = controller.save_document(doc.filename, edited_text)
                    if save_res['success']:
                        st.success("文档已同步")
                        st.rerun()
                    else:
                        st.error(save_res['error'])
            
            with tool_cols[1]:
                if st.button("🔗 空间", key=f"enter_holographic_{doc.filename}", use_container_width=True):
                    st.session_state['selected_document'] = doc.filename
                    st.rerun()
            
            with tool_cols[2]:
                # 状态切换：归档/还原
                if doc.deprecated:
                    if st.button("♻️", key=f"restore_doc_{doc.filename}", use_container_width=True, help="还原文档"):
                        controller.set_document_deprecated(doc.filename, False)
                        st.rerun()
                else:
                    if st.button("📦", key=f"archive_doc_{doc.filename}", use_container_width=True, help="归档文档"):
                        controller.set_document_deprecated(doc.filename, True)
                        st.rerun()
            
            with tool_cols[3]:
                # 删除按钮 (🗑️ 代表删除)
                if st.button("🗑️", key=f"delete_forever_{doc.filename}", use_container_width=True, help="永久删除"):
                    st.session_state[f"confirm_del_{doc.filename}"] = True
                    st.rerun()
            
            with tool_cols[4]:
                st.markdown('<div style="font-size: 0.75rem; color: var(--text-secondary); text-align: right; padding-top: 8px;">✨ 支持实时编辑 | 样式已对齐</div>', unsafe_allow_html=True)
        else:
            st.error("量子链加载失败")
        
        if st.session_state.get(f"confirm_del_{doc.filename}", False):
            st.warning(f"⚠️ 确定要永久删除 {doc.title} 吗？")
            c1, c2 = st.columns(2)
            if c1.button("确认删除", key=f"yes_{doc.filename}"):
                res = controller.delete_document(doc.filename)
                if res['success']: st.success("已删除"); st.rerun()
                else: st.error(res['error'])
            if c2.button("取消", key=f"no_{doc.filename}"):
                del st.session_state[f"confirm_del_{doc.filename}"]
                st.rerun()
                
        st.markdown("<br>", unsafe_allow_html=True)


def _render_unified_workspace(controller: DocumentManagementController, doc_id: str):
    """渲染统一的全息规约工作空间 (One-Page Detail)"""
    # 顶部导航 & 快捷操作
    col_back, col_actions = st.columns([1, 4])
    with col_back:
        if st.button("⬅️ 返回矩阵", use_container_width=True):
            st.session_state['selected_document'] = None
            st.rerun()
            
    # 加载文档内容
    doc_result = controller.read_document(doc_id)
    if not doc_result['success']:
        st.error(doc_result['error'])
        # 如果加载失败，清除选择并返回
        if st.button("返回列表"):
            st.session_state['selected_document'] = None
            st.rerun()
        return
        
    content = doc_result['content']
    metadata = doc_result['metadata']
    
    # 标题栏 (带有版本和分类)
    st.markdown(f"### 📄 {metadata.title if metadata.title else doc_id}")
    
    # 核心编辑/全息预览区 (Side-by-Side)
    edit_col, preview_col = st.columns([1, 1])
    
    with edit_col:
        st.markdown("#### 🛠️ 规约源代码")
        edited_content = st.text_area("Markdown Source", value=content, height=500, label_visibility="collapsed", key=f"edit_{doc_id}")
        
        c1, c2, c3 = st.columns(3)
        if c1.button("💾 同步到本地", type="primary", use_container_width=True):
            res = controller.save_document(doc_id, edited_content)
            if res['success']: st.success("资产已同步"); st.rerun()
            else: st.error(res['error'])
        if c2.button("🔄 复位数据转换", use_container_width=True):
            st.rerun()
            
    with preview_col:
        st.markdown("#### 👁️ 全息实时预览")
        # 先处理文档引用，再处理配置引用
        rendered_content = _highlight_doc_refs_in_markdown(controller, edited_content, doc_id)
        rendered_content_with_config = _highlight_config_refs_in_markdown(controller, rendered_content, doc_id)
        st.markdown(f"""
        <div class="doc-content-box doc-preview-box" style="height: 500px; overflow-y: auto;">
            {rendered_content_with_config}
        </div>
        """, unsafe_allow_html=True)
        
        # 配置引用快捷按钮区域
        refs_info = controller.get_document_references(doc_id)
        if refs_info['references']['config_refs']:
            st.markdown("---")
            st.caption("⚙️ **配置引用快捷跳转**（悬停查看值，点击跳转到配置中心定位）")
            config_ref_cols = st.columns(min(len(refs_info['references']['config_refs']), 4))
            for idx, config_ref in enumerate(refs_info['references']['config_refs'][:8]):  # 最多显示8个
                config_path = config_ref.replace('@config.', '')
                config_value = controller.resolve_config_ref_link(config_path)
                display_value = str(config_value)[:30] + "..." if config_value and len(str(config_value)) > 30 else (str(config_value) if config_value else "未找到")
                with config_ref_cols[idx % len(config_ref_cols)]:
                    if st.button(f"⚙️ {config_path.split('.')[-1]}", key=f"ws_config_link_{config_ref}_{doc_id}_{idx}", use_container_width=True, help=f"{config_ref} = {display_value}"):
                        # 设置锚点并跳转到配置中心
                        st.session_state['config_center_active'] = True
                        st.session_state['active_anchor_cfg'] = config_path
                        st.session_state['selected_document'] = None
                        st.rerun()
            if len(refs_info['references']['config_refs']) > 8:
                st.caption(f"... 还有 {len(refs_info['references']['config_refs']) - 8} 个配置引用")

    # Impact Intelligence & Functional Merge
    st.divider()
    
    # 获取引用信息（包含 related_registry）
    refs_info = controller.get_document_references(doc_id)
    
    tab_merge, tab_impact = st.tabs(["🌐 功能合并 (Functional Merge)", "🔗 影响矩阵 (System Impact)"])
    
    with tab_merge:
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown("##### 🧬 逻辑模块关联")
            related_mods = refs_info.get('related_registry', {}).get('modules', [])
            if related_mods:
                for mod in related_mods:
                    status = "✅" if mod['active'] else "⛔"
                    st.markdown(f"""<div style="padding: 10px; background: rgba(0,217,255,0.05); border: 1px solid rgba(0,217,255,0.2); border-radius: 8px; margin-bottom: 8px;">
                        {status} <b>{mod['id']}</b><br><small>{mod['name']}</small></div>""", unsafe_allow_html=True)
            else: st.caption("未检测到直接关联模块")
        
        with m2:
            st.markdown("##### 🌌 全息格局关联")
            related_pats = refs_info.get('related_registry', {}).get('patterns', [])
            if related_pats:
                for pat in related_pats:
                    status = "✅" if pat['active'] else "⛔"
                    st.markdown(f"""<div style="padding: 10px; background: rgba(123,97,255,0.05); border: 1px solid rgba(123,97,255,0.2); border-radius: 8px; margin-bottom: 8px;">
                        {status} <b>{pat['id']}</b><br><small>{pat['name_cn'] or pat['name']}</small></div>""", unsafe_allow_html=True)
            else: st.caption("未检测到直接关联格局")
            
        with m3:
            st.markdown("##### ⚙️ 配置权重索引")
            active_anchor = st.session_state.get('active_anchor_cfg')
            if refs_info['references']['config_refs']:
                for cfg in sorted(refs_info['references']['config_refs']):
                    is_anchored = (cfg == active_anchor)
                    config_value = controller.resolve_config_ref_link(cfg)
                    display_value = str(config_value)[:40] + "..." if config_value and len(str(config_value)) > 40 else (str(config_value) if config_value else "未找到")
                    if is_anchored:
                        st.markdown(f'<div style="padding: 5px; border: 1px solid var(--success); border-radius: 4px; background: rgba(0,230,118,0.1); margin-bottom: 5px;"><code style="color: #00E676;">@config.{cfg}</code> <span style="font-size: 10px; color: var(--success);">(ANCHORED)</span><br><small style="color: #8B949E;">值: {display_value}</small></div>', unsafe_allow_html=True)
                    else:
                        if st.button(f"⚙️ {cfg}", key=f"cfg_link_{cfg}_{doc_id}", use_container_width=True, help=f"@{cfg} = {display_value}"):
                            st.session_state['config_center_active'] = True
                            st.session_state['active_anchor_cfg'] = cfg
                            st.session_state['selected_document'] = None
                            st.rerun()
                
                # 如果有锚点且已显示，清理状态
                if active_anchor:
                    del st.session_state['active_anchor_cfg']
            else: st.caption("无配置索引")

    with tab_impact:
        i1, i2 = st.columns(2)
        with i1:
            st.markdown("##### 📤 向外引用")
            if refs_info['references']['documents']:
                for r in refs_info['references']['documents']:
                    if st.button(f"📄 {r}", key=f"jump_{r}_{doc_id}", use_container_width=True):
                        st.session_state['selected_document'] = r
                        st.rerun()
            else: st.caption("该文档独立运行")
            
        with i2:
            st.markdown("##### 📥 被引用压力")
            if refs_info['referenced_by']:
                impact_score = len(refs_info['referenced_by']) * 2
                st.metric("核心指数 (CORE INDEX)", impact_score)
                for r in refs_info['referenced_by']:
                    st.caption(f"← {r.title}")
            else: st.caption("目前处于叶子节点")


def _highlight_config_refs_in_markdown(controller: DocumentManagementController, content: str, current_filename: str) -> str:
    """
    在Markdown内容中高亮显示配置引用（@config.*），并添加悬停提示和点击定位功能
    
    Args:
        controller: 文档管理控制器
        content: 文档内容（已处理过文档引用）
        current_filename: 当前文档的文件名
        
    Returns:
        处理后的Markdown内容（配置引用被高亮为可点击的HTML）
    """
    import re
    
    # 解析配置引用
    refs_info = controller.get_document_references(current_filename)
    config_refs = refs_info['references']['config_refs']
    
    if not config_refs:
        return content
    
    # 为每个配置引用创建可点击的链接
    processed_content = content
    processed_positions = set()
    
    # 按长度排序（先匹配长的路径，避免短路径误匹配）
    sorted_config_refs = sorted(config_refs, key=len, reverse=True)
    
    for config_ref in sorted_config_refs:
        # 解析配置路径（例如 @config.gating.weak_self_limit -> gating.weak_self_limit）
        config_path = config_ref.replace('@config.', '')
        
        # 获取配置值
        config_value = controller.resolve_config_ref_link(config_path)
        if config_value:
            display_value = str(config_value)[:50]  # 限制显示长度
            if len(str(config_value)) > 50:
                display_value += "..."
        else:
            display_value = "未找到配置值"
        
        # 匹配模式：@config.xxx（完整匹配）
        pattern = rf'@config\.{re.escape(config_path)}\b'
        
        # 查找所有匹配位置
        for match in re.finditer(pattern, processed_content):
            start, end = match.span()
            
            # 检查是否已被处理（避免重复替换）
            is_processed = False
            for p_start, p_end in processed_positions:
                if not (end <= p_start or start >= p_end):
                    is_processed = True
                    break
            
            if is_processed:
                continue
            
            # 标记为已处理
            processed_positions.add((start, end))
            
            # 创建可点击的HTML元素（带悬停提示和点击跳转）
            config_id = f"config_ref_{hash(config_ref)}_{start}"
            # 转义HTML特殊字符
            safe_display_value = display_value.replace('"', '&quot;').replace("'", '&#39;')
            safe_config_path = config_path.replace('"', '&quot;').replace("'", '&#39;')
            replacement = (
                f'<span class="config-ref-link" '
                f'id="{config_id}" '
                f'data-config-path="{safe_config_path}" '
                f'style="color: #00E676; font-weight: bold; text-decoration: underline; cursor: pointer; '
                f'background: rgba(0, 230, 118, 0.1); padding: 2px 4px; border-radius: 3px; '
                f'transition: background 0.2s;" '
                f'onmouseover="this.style.background=\'rgba(0, 230, 118, 0.2)\';" '
                f'onmouseout="this.style.background=\'rgba(0, 230, 118, 0.1)\';" '
                f'onclick="event.preventDefault(); window.parent.postMessage({{type: \'streamlit:configLink\', configPath: \'{safe_config_path}\'}}, \'*\');" '
                f'title="配置值: {safe_display_value} | 点击跳转到配置中心定位">'
                f'{config_ref}'
                f'</span>'
            )
            
            # 替换（从后往前，避免位置偏移）
            processed_content = processed_content[:start] + replacement + processed_content[end:]
            
            # 更新已处理位置（因为内容长度变了）
            offset = len(replacement) - len(config_ref)
            processed_positions = {
                (s + offset if s > start else s, e + offset if e > start else e)
                for s, e in processed_positions if (s, e) != (start, end)
            }
        
    return processed_content


def _highlight_doc_refs_in_markdown(controller: DocumentManagementController, content: str, current_filename: str) -> str:
    """终极版：自动化全息链路解析
    1. 自动识别文档 ID 及相关术语
    2. 支持 QGA-HR -> QGA_HR 等模糊转换
    3. 识别 @config 锚点
    """
    import re
    from urllib.parse import quote
    
    # 基础 Markdown 转类 HTML (改为简约排版)
    html_content = content.replace("###", '<div style="font-size: 1.05rem; font-weight: bold; margin: 15px 0 8px 0; color: var(--text-primary);">')
    html_content = html_content.replace("##", '<div style="font-size: 1.15rem; font-weight: bold; margin: 20px 0 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 5px; color: var(--text-primary);">')
    html_content = html_content.replace("# ", '<div style="font-size: 1.3rem; font-weight: bold; margin: 25px 0 15px 0; color: var(--primary);">')
    # 闭合 div
    html_content = html_content.replace("\n", "</div>\n")
    html_content = html_content.replace("\n", "<br>")
    
    # 获取所有文档名用于精准匹配
    all_docs = [d.filename for d in controller.get_documents_by_category(category=None)]
    
    # 1. 解析文档引用 (如 QGA-HR V3.0, FDS_MODELING_SPEC, etc.)
    # 匹配模式：大写字母开头，包含下划线、连字符或点号的标识符
    # 或者显式的 .md 结尾
    ref_pattern = r'\b([A-Z][A-Z0-9_\-\.]+(?:\s?V\d+\.\d+)?(?:\.md)?)\b'
    
    def intelligent_doc_linker(match):
        raw_text = match.group(1)
        # 归一化处理：转大写，空格/连字符转下划线
        norm_text = raw_text.strip().upper().replace("-", "_").replace(" ", "_")
        
        # 尝试匹配
        target_filename = None
        
        # 策略A：完全匹配
        if raw_text in all_docs:
            target_filename = raw_text
        # 策略B：加 .md 匹配
        elif f"{raw_text}.md" in all_docs:
            target_filename = f"{raw_text}.md"
        # 策略C：归一化匹配 (QGA-HR V3.0 -> QGA_HR_V3.0.md)
        else:
            for doc_name in all_docs:
                if norm_text in doc_name.upper():
                    target_filename = doc_name
                    break
        
        if target_filename:
            if target_filename == current_filename:
                return f'<span style="color: #00D9FF; border-bottom: 1px dashed;">{raw_text}</span>'
            return f'<a href="?selected_doc={quote(target_filename)}" target="_self" style="color: #00D9FF; text-decoration: underline;">{raw_text}</a>'
        
        return raw_text

    # 预处理：先处理 @config 免得被宏观正则吃掉
    # 2. 高亮并链接配置项
    cfg_pattern = r'(@config\.([a-z0-9_\.]+))'
    from core.config import config
    
    def link_cfg(match):
        full_cfg = match.group(1)
        cfg_key = match.group(2)
        
        # 尝试获取实时数值
        try:
            val = config.resolve_config_ref(full_cfg)
            if isinstance(val, (int, float)):
                val_str = f"{val:.2f}" if isinstance(val, float) else str(val)
                tooltip = f"当前值: {val_str}"
            else:
                tooltip = f"配置项: {full_cfg}"
        except:
            tooltip = "解析失败"
            
        return f'<a href="?selected_doc={quote(current_filename)}&anchor_cfg={quote(cfg_key)}" target="_self" class="cfg-link" style="color: #00E676; text-decoration: none;" title="{tooltip}"><code style="color: #00E676; background: rgba(0,230,118,0.05); padding: 2px 4px; border-radius: 4px; border: 1px solid rgba(0,230,118,0.15);">{full_cfg}</code></a>'
    
    html_content = re.sub(cfg_pattern, link_cfg, html_content)
    
    # 执行文档链接解析
    html_content = re.sub(ref_pattern, intelligent_doc_linker, html_content)
    
    # 3. 高亮模块 ID (特殊处理)
    mod_pattern = r'\b(MOD_\d+)\b'
    html_content = re.sub(mod_pattern, r'<span style="color: #FFD600; font-weight: bold;">\1</span>', html_content)

    return html_content


# Main entry point
if __name__ == "__main__":
    render()
