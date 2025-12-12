import streamlit as st
import time
from datetime import datetime as dt
from core.profile_manager import ProfileManager
from learning.bio_miner import BioMiner
from learning.web_hunter import WebHunter
from learning.db import LearningDB

def render_profile_section():
    """
    Renders the Profile Management Expander.
    Handles Profile List, Bio Miner, and Web Hunter.
    Syncs selected profile to st.session_state for the Input Form to pick up.
    """
    pm = ProfileManager()
    
    with st.expander("📂 档案管理 (Archives)", expanded=True):
        # --- Profile & Bio Import Tabs ---
        tab_prof, tab_bio, tab_web = st.tabs(["👥 档案管理 (Profiles)", "🧬 名人传记导入 (Bio Miner)", "🌐 全网搜捕 (Web Hunter)"])
        
        with tab_prof:
            _render_profile_list(pm)

        with tab_bio:
            _render_bio_miner()

        with tab_web:
            _render_web_hunter(pm)

def _render_profile_list(pm):
    all_profiles = pm.get_all()
    # Unique names
    profile_names = ["(New / Custom)"] + [f"{p.get('name', 'Unknown')} ({p.get('gender','?')})" for p in all_profiles]
    
    selected_profile_str = st.selectbox("选择档案 (Select Profile)", profile_names)
    
    loaded_data = None
    if selected_profile_str != "(New / Custom)":
        p_name = selected_profile_str.split(" (")[0]
        loaded_data = next((p for p in all_profiles if p.get('name') == p_name), None)
        
        # Sync to Session State if changed
        if st.session_state.get('last_profile') != selected_profile_str and loaded_data:
            _sync_profile_to_session(loaded_data)
            st.session_state['last_profile'] = selected_profile_str
            st.rerun()
    else:
        # Reset if switching to New
        if st.session_state.get('last_profile') != selected_profile_str:
            st.session_state['last_profile'] = selected_profile_str
            # FIX: Explicitly clear inputs so user can type new name
            st.session_state['input_name'] = "某人"
            st.session_state['input_gender'] = "男"
            st.session_state['input_date'] = dt(1990, 1, 1)
            st.session_state['input_time'] = 12
            st.rerun()

    # --- Save / Delete Actions ---
    col_save, col_del = st.columns([1,1])
    with col_save:
        if st.button("💾 保存当前", key="btn_save"):
            # Retrieve from Session State (Input Form)
            s_name = st.session_state.get('input_name')
            s_gender = st.session_state.get('input_gender')
            s_date = st.session_state.get('input_date')
            s_time = st.session_state.get('input_time')
            
            if s_name and s_name != "某人":
                ok, msg = pm.add_profile(s_name, s_gender, s_date.year, s_date.month, s_date.day, s_time)
                if ok: 
                    st.success(f"已保存: {s_name}") 
                    time.sleep(0.5)
                    st.rerun()
            else:
                st.error("请输入有效姓名")
            
    with col_del:
        if loaded_data and st.button("🗑️ 删除选中", key="btn_del"):
            ok, msg = pm.delete_profile(loaded_data['id'])
            if ok:
                st.success("已删除")
                time.sleep(0.5)
                st.rerun()

def _sync_profile_to_session(loaded_data):
    st.session_state['input_name'] = loaded_data['name']
    st.session_state['input_gender'] = loaded_data['gender']
    try:
        d_obj = dt(int(loaded_data['year']), int(loaded_data['month']), int(loaded_data['day']))
        st.session_state['input_date'] = d_obj
    except:
        pass
    st.session_state['input_time'] = int(loaded_data['hour'])

def _render_bio_miner():
    st.caption("🤖 利用 AI 自动从传记文本中提取核心人生事件，作为训练系统的“真值数据”。")
    bio_name = st.text_input("人物姓名", placeholder="e.g. Steve Jobs")
    bio_year = st.number_input("出生年份 (用于对齐时间轴)", 1900, 2025, 1980)
    bio_text = st.text_area("传记文本 / Wiki", height=150, placeholder="粘贴传记内容...")
    
    if st.button("🔬 启动生平分析 (Analyze Bio)"):
        if not bio_text or len(bio_text) < 50:
            st.warning("文本太短")
        else:
            with st.spinner("AI 正在阅读传记并量化人生..."):
                miner = BioMiner(ollama_host=st.session_state.get('ollama_host'))
                events = miner.analyze_biography(bio_text, bio_year)
                
                st.session_state['bio_events_cache'] = events
                st.success(f"提取成功! 发现 {len(events)} 个关键事件")
    
    # Show results & cleanup
    if 'bio_events_cache' in st.session_state and st.session_state['bio_events_cache']:
        events = st.session_state['bio_events_cache']
        st.write(events) # JSON view
        
        # Rectification Tool (Simplified)
        if st.checkbox("🔍 启用【生时校对】 (Time Rectification)"):
             # Logic to reverse engineer birth hour based on events
             pass # Kept simple for now as it relies on Trajectory Engine which we haven't modularized fully here? 
                  # Actually Rectification logic is complex. We'll leave the UI hooks.
             st.info("校对功能需要调用后台模拟... (Refactored: Please implement Rectification Module)")

        # Import Button
        if st.button("📥 导入此数据作为【真值】"):
            db = LearningDB()
            count = 0
            for e in events:
                yr = e.get('year')
                # Simplistic mapping
                asp = e.get('aspect')
                map_asp = {"Career": "事业 (Career)", "Wealth": "财富 (Wealth)", "Health": "健康 (Health)", "Marriage": "人际 (Friendship)"}
                final_asp = map_asp.get(asp, "总运势 (Total)")
                
                if yr:
                    db.add_feedback(yr, final_asp, e.get('score', 50), e.get('note', ''))
                    count += 1
            
            st.success(f"成功导入 {count} 条真值数据！")
            st.session_state['bio_events_cache'] = None
            time.sleep(1); st.rerun()

def _render_web_hunter(pm):
    st.caption("🤖 自动搜寻网络上的八字案例，并提取其人生轨迹。")
    w_name = st.text_input("目标人物 Key", placeholder="e.g. 马云 八字")
    
    if st.button("🚀 搜索并抓取 (Hunt Bazi)"):
        with st.spinner(f"正在全网搜捕【{w_name}】的命理数据..."):
             hunter = WebHunter(ollama_host=st.session_state.get('ollama_host'))
             result = hunter.hunt(w_name)
             
             if result:
                 st.success(f"捕获成功！来源: {result.get('source_url')}")
                 st.session_state['hunt_result'] = result
             else:
                 st.error("未找到有效的八字分析文章 (或抓取失败)")

    if 'hunt_result' in st.session_state:
        res = st.session_state['hunt_result']
        st.json(res)
        
        if st.button("💾 存入数据库"):
             # 1. Add Profile
             try:
                 nm = res.get('name', w_name)
                 yr = res.get('birth_year')
                 mo = res.get('birth_month')
                 dy = res.get('birth_day')
                 hr = res.get('birth_hour') or 12
                 gen = res.get('gender', '男')
                 
                 if yr and mo and dy:
                     pm.add_profile(nm, gen, yr, mo, dy, hr)
                     # 2. Add Feedbacks
                     db = LearningDB()
                     events = res.get('events', [])
                     for e in events:
                         asp = e.get('aspect')
                         map_asp = {"Career": "事业 (Career)", "Wealth": "财富 (Wealth)"}
                         final_asp = map_asp.get(asp, "总运势 (Total)")
                         db.add_feedback(e.get('year'), final_asp, e.get('score', 50), e.get('note','From Web'))
                         
                     st.success("全部入库完成！")
                 else:
                     st.error("抓取的数据日期不全，无法入库")
             except Exception as e:
                 st.error(f"Save Error: {e}")
