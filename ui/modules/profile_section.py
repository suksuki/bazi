import streamlit as st
import time
from datetime import datetime as dt
from core.profile_manager import ProfileManager
from lunar_python import Solar

def render_profile_section():
    """
    Simplified Profile Management with Bazi Quick Test.
    Removed: Bio Miner, Web Hunter
    Added: Quick Bazi Input
    """
    pm = ProfileManager()
    
    with st.expander("📂 档案管理 (Archives)", expanded=True):
        # --- Tabs: Profile Management & Quick Bazi Test ---
        tab_prof, tab_bazi = st.tabs(["👥 档案管理 (Profiles)", "⚡ 八字测试 (Quick Test)"])
        
        with tab_prof:
            _render_profile_list(pm)

        with tab_bazi:
            _render_bazi_quick_test()

def _render_profile_list(pm):
    """Existing profile management functionality"""
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
            # Clear inputs so user can type new name
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
    """Sync loaded profile data to session state"""
    st.session_state['input_name'] = loaded_data['name']
    st.session_state['input_gender'] = loaded_data['gender']
    try:
        d_obj = dt(int(loaded_data['year']), int(loaded_data['month']), int(loaded_data['day']))
        st.session_state['input_date'] = d_obj
    except:
        pass
    st.session_state['input_time'] = int(loaded_data['hour'])

def _render_bazi_quick_test():
    """
    NEW: Quick Bazi Test - Single input field with auto-parsing
    User inputs complete 8-character bazi string: "乙未丙戌壬戌辛亥"
    System auto-parses into 4 pillars
    """
    st.caption("⚡ 快速测试：输入完整八字（8个字），系统自动识别四柱")
    
    # Single input field for complete bazi
    bazi_input = st.text_input(
        "完整八字 (8个字符，可带空格)", 
        value="乙未 丙戌 壬戌 辛亥",
        placeholder="例: 乙未丙戌壬戌辛亥 或 乙未 丙戌 壬戌 辛亥",
        max_chars=15,  # 8 chars + spaces
        key="bazi_full_input",
        help="年月日时共8个字，可用空格分隔"
    )
    
    # Auto-parse and display
    parsed = _parse_bazi_string(bazi_input)
    
    if parsed['valid']:
        # Display parsed pillars in a nice format
        st.markdown("**识别结果**:")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"<div style='text-align: center; padding: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; color: white; font-size: 1.2em; font-weight: bold;'>{parsed['year']}</div>", unsafe_allow_html=True)
            st.caption("年柱")
        with col2:
            st.markdown(f"<div style='text-align: center; padding: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; color: white; font-size: 1.2em; font-weight: bold;'>{parsed['month']}</div>", unsafe_allow_html=True)
            st.caption("月柱")
        with col3:
            st.markdown(f"<div style='text-align: center; padding: 10px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 8px; color: white; font-size: 1.2em; font-weight: bold;'>{parsed['day']}</div>", unsafe_allow_html=True)
            st.caption("日柱 ⭐")
        with col4:
            st.markdown(f"<div style='text-align: center; padding: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; color: white; font-size: 1.2em; font-weight: bold;'>{parsed['hour']}</div>", unsafe_allow_html=True)
            st.caption("时柱")
        
        # Show day master
        day_master = parsed['day'][0]
        st.info(f"日主 (Day Master): **{day_master}** ({_get_element_name(day_master)})")
    else:
        st.warning(f"⚠️ {parsed['error']}")
        st.caption("请输入8个有效的天干地支字符，如: 乙未丙戌壬戌辛亥")
    
    # Gender selection
    gender = st.radio("性别", ["男", "女"], horizontal=True, key="bazi_gender")
    
    # Quick Test Button
    if st.button("🚀 快速排盘 (Quick Calculate)", type="primary", disabled=not parsed['valid']):
        # Reverse calculate approximate date
        try:
            approx_date = _reverse_calculate_date(
                parsed['year'], parsed['month'], parsed['day'], parsed['hour']
            )
            
            # Set session state with calculated values
            st.session_state['input_name'] = f"八字测试-{day_master}"
            st.session_state['input_gender'] = gender
            st.session_state['input_date'] = approx_date['date']
            st.session_state['input_time'] = approx_date['hour']
            
            # Store the original bazi for display
            st.session_state['bazi_input'] = {
                'year': parsed['year'],
                'month': parsed['month'],
                'day': parsed['day'],
                'hour': parsed['hour']
            }
            
            # Trigger calculation
            st.session_state['calc_active'] = True
            
            st.success(f"✅ 八字已加载: {parsed['year']} {parsed['month']} {parsed['day']} {parsed['hour']}")
            st.info(f"📅 近似日期: {approx_date['date'].strftime('%Y-%m-%d')} {approx_date['hour']}:00")
            time.sleep(0.8)
            st.rerun()
            
        except Exception as e:
            st.error(f"计算错误: {e}")
    
    # Show example with copy buttons
    with st.expander("📖 示例八字 (点击复制)", expanded=False):
        st.markdown("**V3.0 财库测试案例 (保证看到🏆)**:")
        
        examples = [
            ("乙未丙戌壬戌辛亥", "水日主+戌财库 → 2024辰年冲开"),
            ("甲子丙寅甲丑丙寅", "木日主+丑土库 → 2015未年冲开"),
            ("庚申丁酉辛未戊子", "金日主+未木库 → 2021丑年冲开"),
            ("乙未戊寅壬午辛亥", "乔布斯八字 → 2011截脚测试"),
            ("甲辰丙子己亥丙寅", "马云八字 → 财库多开"),
        ]
        
        for bazi, desc in examples:
            col_text, col_btn = st.columns([3, 1])
            with col_text:
                st.code(bazi, language="text")
                st.caption(desc)
            with col_btn:
                if st.button("📋", key=f"copy_{bazi}", help="点击自动填充"):
                    st.session_state['bazi_full_input'] = bazi
                    st.rerun()

def _parse_bazi_string(input_str):
    """
    Parse bazi input string into 4 pillars.
    Accepts formats:
    - "乙未丙戌壬戌辛亥" (no spaces)
    - "乙未 丙戌 壬戌 辛亥" (with spaces)
    """
    if not input_str:
        return {'valid': False, 'error': '请输入八字'}
    
    # Remove spaces
    cleaned = input_str.replace(' ', '').replace('　', '')  # Remove both space types
    
    # Check length
    if len(cleaned) != 8:
        return {'valid': False, 'error': f'长度错误：需要8个字符，当前{len(cleaned)}个'}
    
    # Valid characters
    gan = "甲乙丙丁戊己庚辛壬癸"
    zhi = "子丑寅卯辰巳午未申酉戌亥"
    
    # Parse each pillar (2 chars each)
    try:
        pillars = {
            'year': cleaned[0:2],
            'month': cleaned[2:4],
            'day': cleaned[4:6],
            'hour': cleaned[6:8]
        }
        
        # Validate each pillar
        for name, pillar in pillars.items():
            stem, branch = pillar[0], pillar[1]
            if stem not in gan:
                return {'valid': False, 'error': f'{name}柱天干错误: {stem}'}
            if branch not in zhi:
                return {'valid': False, 'error': f'{name}柱地支错误: {branch}'}
        
        return {
            'valid': True,
            **pillars
        }
        
    except Exception as e:
        return {'valid': False, 'error': f'解析错误: {str(e)}'}

def _get_element_name(gan_char):
    """Get element name in Chinese for a Gan character"""
    element_map = {
        '甲': '木', '乙': '木',
        '丙': '火', '丁': '火',
        '戊': '土', '己': '土',
        '庚': '金', '辛': '金',
        '壬': '水', '癸': '水'
    }
    return element_map.get(gan_char, '?')

def _reverse_calculate_date(year_pz, month_pz, day_pz, hour_pz):
    """
    Reverse calculate approximate birth date from Bazi pillars.
    This is a simplified version - uses a recent 60-year cycle.
    """
    try:
        # Ganzi cycle mapping (simplified)
        gan_chars = "甲乙丙丁戊己庚辛壬癸"
        zhi_chars = "子丑寅卯辰巳午未申酉戌亥"
        
        # Extract year stem and branch
        year_stem = year_pz[0]
        year_branch = year_pz[1]
        
        # Find year in recent cycle (1924-2043 covers most test cases)
        base_year = 1924  # 甲子年
        
        year_stem_idx = gan_chars.index(year_stem)
        year_branch_idx = zhi_chars.index(year_branch)
        
        # Calculate offset in 60-year cycle
        # Stem cycles every 10 years, Branch every 12
        # Find the year where both match
        for offset in range(120):  # Search 2 full cycles
            test_year = base_year + offset
            if (offset % 10 == year_stem_idx) and (offset % 12 == year_branch_idx):
                # Found a matching year
                # Use mid-year as approximation
                result_year = test_year
                break
        else:
            # Fallback to a default
            result_year = 1990
        
        # Extract month branch for season estimation
        month_branch = month_pz[1]
        month_map = {
            '寅': 2, '卯': 3, '辰': 4, '巳': 5, '午': 6, '未': 7,
            '申': 8, '酉': 9, '戌': 10, '亥': 11, '子': 12, '丑': 1
        }
        approx_month = month_map.get(month_branch, 6)
        
        # Extract hour branch
        hour_branch = hour_pz[1]
        hour_map = {
            '子': 0, '丑': 2, '寅': 4, '卯': 6, '辰': 8, '巳': 10,
            '午': 12, '未': 14, '申': 16, '酉': 18, '戌': 20, '亥': 22
        }
        approx_hour = hour_map.get(hour_branch, 12)
        
        return {
            'date': dt(result_year, approx_month, 15),  # Use mid-month
            'hour': approx_hour
        }
        
    except Exception as e:
        # Fallback to default
        return {
            'date': dt(1990, 6, 15),
            'hour': 12
        }
