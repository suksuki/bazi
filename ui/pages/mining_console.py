import streamlit as st
import pandas as pd
import json
import time
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from service.case_db import CaseDatabase
from service.rule_db import RuleDatabase
from service.processor import ContentProcessor
from service.sanitizer import Sanitizer
from service.web_hunter import WebHunter
from core.config_manager import ConfigManager

def render():
    st.set_page_config(page_title="Crimson Vein 挖掘控制台", layout="wide")
    
    st.title("⛏️ 实战挖掘控制台 (Mining Console)")
    st.caption("项目代号：Crimson Vein | 核心目标：从非结构化互联网数据中提炼真实物理参数")

    # Initialize Services
    case_db = CaseDatabase()
    rule_db = RuleDatabase()
    processor = ContentProcessor()
    
    # Main Layout
    tab_ops, tab_analysis = st.tabs(["🔨 挖掘操作 (Operations)", "🧠 挖掘后分析 (Analysis)"])

    # ==========================================
    # Tab 1: Mining Operations (挖掘操作)
    # ==========================================
    with tab_ops:
        col_op_l, col_op_r = st.columns([2, 1])
        
        with col_op_l:
            st.subheader("1. 投喂数据源 (Feed Data)")
            
            source_type = st.radio("选择来源类型", ["🏆 名人/百科狩猎 (VIP Hunter)", "🤖 全自动搜猎 (Auto-Pilot)", "🌐 Web URL (自动抓取)", "📝 文本粘贴 (手动)", "📂 本地文件 (批量)"], horizontal=True)
            
            # --- Type 1: Celebrity Hunter (Dedicated) ---
            if source_type == "🏆 名人/百科狩猎 (VIP Hunter)":
                st.info("🎯 专注于【Baike/Wiki 生平】+【名家排盘】的定向挖掘。")
                st.markdown("此模式将忽略论坛和本地文件，直接搜索名人百科与排盘分析。")
                
                # Dictionary Status
                vip_count = 0
                dict_path = "data/dictionaries/celebrities.txt"
                if os.path.exists(dict_path):
                    with open(dict_path, "r") as f:
                        vip_count = len([l for l in f if l.strip() and not l.startswith("#")])
                        
                st.write(f"#### 📜 目标字典 (Target Dictionary)")
                st.caption(f"已加载: **{vip_count}** 位 | 路径: `{dict_path}`")
                
                # Preview
                preview = []
                if os.path.exists(dict_path):
                     with open(dict_path) as f: 
                        preview = [l.strip() for l in f if l.strip() and not l.startswith("#")][:5]
                st.code("\n".join(preview)+"\n...", language="text")
                
                cycles = st.slider("目标数量 (Targets)", 1, 20, 5, help="每次任务随机抽取的名人数量。")
                
                if st.button("🏹 启动猎头行动 (Start Hunter)", type="primary"):
                    try:
                        from learning.db import LearningDB
                        ldb = LearningDB()
                    except ImportError: 
                        ldb = None
                        st.error("DB Load Failed")
                    
                    if ldb:
                        payload = {"type": "auto_mine", "cycles": cycles, "mode": "celebrity_only"}
                        ldb.create_job("auto_mine", target_file="VIP-Hunter-Job", payload=payload)
                        st.success(f"✅ 名人狩猎已启动 (目标: {cycles}人)！")

            # --- Type 2: Auto-Pilot (Mixed) ---
            elif source_type == "🤖 全自动搜猎 (Auto-Pilot)":
                st.info("🚀 启动混合搜猎模式。策略：随机名人 -> 本地扫描 -> 论坛深潜 -> 关键词搜索 (Round Robin)。")
                from service.auto_miner import AutoMiner

                st.write("#### 📡 搜索指令集")
                st.code("\n".join(AutoMiner.SEARCH_KEYWORDS[:3]) + "\n...", language="text")
                
                cycles = st.slider("执行周期 (Cycles)", 1, 10, 3)
                
                # Configurable Local Mode
                cm = ConfigManager()
                current_local = cm.get("auto_miner_force_local", False)
                use_local_regex = st.checkbox("⚡ 纯本地极速模式 (仅正则)", value=current_local, help="影响本地文件的处理方式。")
                
                if st.button("🔴 启动混合集群 (Engage Mixed Mode)", type="primary"):
                    cm.save_config("auto_miner_force_local", use_local_regex)
                    try:
                        from learning.db import LearningDB
                        ldb = LearningDB()
                    except ImportError: ldb = None
                        
                    if ldb:
                        payload = {"type": "auto_mine", "cycles": cycles, "mode": "mixed"}
                        ldb.create_job("auto_mine", target_file="Auto-Pilot-Mixed", payload=payload)
                        st.success("✅ 混合搜猎任务已启动！")

            elif source_type == "🌐 Web URL (自动抓取)":
                st.info("适用于：博客文章、名人传记页、论坛帖子页。")
                url_input = st.text_input("目标 URL", placeholder="https://www.astro.com/...")
                
                if st.button("🕷️ 启动猎人 (Deploy Hunter)", type="primary", disabled=not url_input):
                    with st.status("正在执行狩猎任务...", expanded=True) as status:
                        st.write("正在连接目标服务器...")
                        hunter = WebHunter()
                        success = hunter.hunt_from_url(url_input)
                        
                        if success:
                            status.update(label="任务完成！", state="complete", expanded=False)
                            st.success("✅ 抓取成功！数据已送入【挖掘后分析】板块。")
                        else:
                            status.update(label="任务失败", state="error")
                            st.error("抓取失败，可能是反爬虫拦截或内容过短。")

            elif source_type == "📝 文本粘贴 (手动)":
                st.info("适用于：快速测试、从视频字幕复制的片段。")
                raw_text = st.text_area("粘贴内容", height=250)
                manual_src = st.text_input("来源备注 (可选)", placeholder="例如：某某大师视频课第3集")
                
                if st.button("🚀 开始处理 (Process)", type="primary", disabled=not raw_text):
                    with st.spinner("正在净化与提取..."):
                        clean_text = Sanitizer.clean_text(raw_text)
                        processor.process_text(clean_text, source_url=f"Manual: {manual_src}")
                        st.success("处理完成！请前往【挖掘后分析】查看。")

            elif source_type == "📂 本地文件 (批量)":
                st.info("从【影音研习】或【古籍学习】已上传的转录文本中挖掘。")
                
                # Import LearningDB for job creation
                try:
                    from learning.db import LearningDB
                    ldb = LearningDB()
                except ImportError:
                    st.error("无法加载 LearningDB。请检查 learning 模块。")
                    ldb = None
                
                if ldb:
                    book_dir = "data/books"
                    if not os.path.exists(book_dir):
                        os.makedirs(book_dir)
                    
                    files = [f for f in os.listdir(book_dir) if f.endswith(".txt")]
                    if not files:
                        st.warning("data/books 目录下没有文本文件。请先去【自我进化】->【影音/古籍】上传。")
                    else:
                        # --- Prepare Data for Editor ---
                        # Use session state to persist selection across reruns if needed, 
                        # but for simple batch action, reconstruction is fine.
                        
                        # --- Robust State Management ---
                        if "file_mining_list" not in st.session_state:
                            # Initial Load
                            file_data = []
                            for f in files:
                                path = os.path.join(book_dir, f)
                                size_kb = os.path.getsize(path) / 1024
                                ftype = "🎥 影音笔记" if "[Video]" in f or "[Media]" in f else "📜 古籍/文本"
                                file_data.append({
                                    "Select": False,
                                    "Filename": f,
                                    "Type": ftype,
                                    "Size (KB)": round(size_kb, 1)
                                })
                            st.session_state["file_mining_list"] = file_data
                        
                        # Use data from session state
                        df_display = pd.DataFrame(st.session_state["file_mining_list"])

                        # --- Controls Toolbar ---
                        c_tool1, c_tool2, c_tool3 = st.columns([1, 1, 2])
                        
                        if c_tool1.button("✅ 全选"):
                            for item in st.session_state["file_mining_list"]:
                                item["Select"] = True
                            st.rerun()
                            
                        if c_tool2.button("⬜ 全不选"):
                            for item in st.session_state["file_mining_list"]:
                                item["Select"] = False
                            st.rerun()
                            
                        sort_opt = c_tool3.selectbox("排序方式", ["Filename", "Size (KB)", "Type"], label_visibility="collapsed")
                        
                        # --- LLM Control ---
                        st.markdown("---")
                        c_llm, c_launch = st.columns([1, 1])
                        
                        use_llm = c_llm.checkbox("🧠 启用 DeepSeek LLM 深度分析 (慢速但精准)", value=False, help="若选中，将调用云端或本地 LLM 进行逐句分析；若不选，仅使用正则极速匹配。")
                        
                        # Apply Sorting strictly for display (Session state order remains stable)
                        if sort_opt == "Size (KB)":
                            df_display = df_display.sort_values(by="Size (KB)", ascending=False)
                        elif sort_opt == "Type":
                            df_display = df_display.sort_values(by="Type")
                        else:
                            df_display = df_display.sort_values(by="Filename")
                        
                        editor_key = "file_mining_editor"
                        
                        # Actual Editor
                        edited_df = st.data_editor(
                            df_display,
                            column_config={
                                "Select": st.column_config.CheckboxColumn("选择", width="small"),
                                "Filename": st.column_config.TextColumn("文件名", width="large"),
                                "Type": st.column_config.TextColumn("类型", width="medium"),
                                "Size (KB)": st.column_config.NumberColumn("大小 (KB)"),
                            },
                            disabled=["Filename", "Type", "Size (KB)"],
                            hide_index=True,
                            use_container_width=True,
                            key=editor_key
                        )
                        
                        # Process Button
                        target_files = edited_df[edited_df["Select"] == True]["Filename"].tolist()
                        
                        st.caption(f"已选择: {len(target_files)} 个文件")
                        
                        if c_launch.button("⛏️ 启动深度挖掘任务 (Start Deep Mining Job)", type="primary", disabled=len(target_files)==0):
                            # SAVE CONFIG FIRST
                            cm = ConfigManager()
                            # If use_llm is Checked, force_local should be False
                            cm.save_config("auto_miner_force_local", not use_llm)
                            
                            count = 0
                            for fname in target_files:
                                payload = {
                                    "type": "case_mine", 
                                    "filename": fname,
                                    "target_db": "cases.db"
                                }
                                ldb.create_job("case_mine", target_file=fname, payload=payload)
                                count += 1
                            
                            st.success(f"🚀 已创建 {count} 个后台任务！")
                            st.info(f"Worker 将在后台读取文件，提取案例并存入 CaseDB。\n模式: {'🔥 深度 LLM 分析' if use_llm else '⚡ 极速正则匹配'}")

        with col_op_r:
            st.subheader("2. 实时监控 (Monitor)")
            with st.container(border=True):
                st.metric("今日已挖掘案例", len(case_db.get_all_cases_meta()), delta="+2")
                st.metric("待审核规则", 0) # TODO: Connect to RuleDB count
                st.markdown("---")
                st.caption("系统日志")
                st.code("System Ready...\nMiner Alpha loaded.\nCaseDB connected.", language="bash")

    # ==========================================
    # Tab 2: Post-Mining Analysis (挖掘后分析)
    # ==========================================
    with tab_analysis:
        sub_tab_cases, sub_tab_rules = st.tabs(["📂 案例库 (Case Library)", "📜 规则库 (Rule Library)"])
        
        # --- Case Library ---
        with sub_tab_cases:
            st.markdown("### 真实八字案例库")
            
            # Load Data
            metadata = case_db.get_all_cases_meta()
            if metadata:
                df_meta = pd.DataFrame(metadata)
                
                # Selection Table
                st.dataframe(
                    df_meta,
                    column_config={
                        "id": st.column_config.TextColumn("ID", width="small"),
                        "name": st.column_config.TextColumn("姓名", width="medium"),
                        "quality_tier": st.column_config.TextColumn("质量等级", width="small"),
                    },
                    use_container_width=True,
                    hide_index=True
                )
                
                col_sel, col_view = st.columns([1, 2])
                with col_sel:
                    selected_case_id = st.selectbox("选择案例查看详情", df_meta['id'].tolist(), format_func=lambda x: f"{x} - {df_meta[df_meta['id']==x]['name'].values[0]}")
                
                if selected_case_id:
                    case = case_db.get_case(selected_case_id)
                    with col_view:
                        with st.container(border=True):
                            c1, c2 = st.columns(2)
                            c1.markdown(f"**姓名**: {case.get('name', 'Unknown')}")
                            c2.markdown(f"**Tier**: {case.get('quality_tier', 'N/A')}")
                            
                            # Safety check for profile
                            profile_data = case.get('profile')
                            if not profile_data:
                                # Fallback for legacy/flat data
                                profile_data = {
                                    "name": case.get('name'),
                                    "gender": case.get('gender'),
                                    "birth_year": case.get('birth_year'),
                                    "birth_date": f"{case.get('birth_year')}-{case.get('birth_month')}-{case.get('birth_day')}",
                                    "birth_time": f"{case.get('birth_hour')}:{case.get('birth_minute')}"
                                }
                            st.json(profile_data, expanded=False)
                            
                            st.markdown("#### 📅 人生大事验证集")
                            st.dataframe(pd.DataFrame(case['life_events']), hide_index=True)
                            
                            st.markdown("#### ✅ 算法验证操作")
                            if st.button("🧪 运行物理内核回测 (Run Kernel Validation)", key="btn_validate", type="primary"):
                                st.toast("正在启动 V32.0 物理引擎...", icon="🔥")
                                time.sleep(1)
                                st.info("正在计算流年能量分布...")
                                time.sleep(1)
                                st.warning("⚠️ 验证引擎尚未连接真实内核 (Mock Result)")
                                st.write("预测结果: 2008年 [压力极高] (匹配度 95%)")
            else:
                st.info("案例库为空，请先去【挖掘操作】进货。")

        # --- Rule Library ---
        with sub_tab_rules:
            st.markdown("### 命理规则知识库")
            st.caption("此处存放从文本中提取的理论逻辑 (如 '伤官见官')。")
            
            conn = rule_db._get_conn()
            try:
                df_rules = pd.read_sql("SELECT * FROM rules", conn)
                st.dataframe(df_rules, use_container_width=True)
            except:
                st.info("规则库为空。")
            conn.close()

if __name__ == "__main__":
    render()
