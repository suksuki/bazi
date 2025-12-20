import streamlit as st
import time
from datetime import datetime as dt
from core.profile_manager import ProfileManager
from lunar_python import Solar

from ui.components.theme import COLORS, GLASS_STYLE

def render_profile_section():
    """
    Simplified Profile Management with Bazi Quick Test.
    """
    pm = ProfileManager()
    
    st.markdown(f"""
        <div style="{GLASS_STYLE} padding: 15px; margin-bottom: 10px; border-left: 4px solid {COLORS['mystic_gold']};">
            <h3 style="color: {COLORS['mystic_gold']}; margin: 0;">📂 档案管理</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # --- Tabs: Profile Management & Quick Bazi Test ---
    tab_prof, tab_bazi = st.tabs(["👥 档案列表", "⚡ 快速测算"])
    
    with tab_prof:
        _render_profile_list(pm)

    with tab_bazi:
        _render_bazi_quick_test()


def _render_profile_list(pm):
    """Profile management with proper save/load functionality"""
    all_profiles = pm.get_all()
    
    # Build profile options: ID -> Display Name mapping
    profile_options = {"new": "(New / Custom)"}
    for p in all_profiles:
        pid = p.get('id', '')
        pname = p.get('name', 'Unknown')
        pgender = p.get('gender', '?')
        profile_options[pid] = f"{pname} ({pgender})"
    
    # Handle pending profile selection (set before widget renders)
    if '_pending_profile_select' in st.session_state:
        pending_id = st.session_state.pop('_pending_profile_select')
        if pending_id in profile_options:
            st.session_state['profile_select_id'] = pending_id
    
    # Get current selected profile ID
    current_id = st.session_state.get('profile_select_id', st.session_state.get('current_profile_id', 'new'))
    if current_id not in profile_options:
        current_id = 'new'
    
    # Profile selection dropdown
    option_list = list(profile_options.keys())
    display_list = list(profile_options.values())
    
    try:
        current_idx = option_list.index(current_id)
    except ValueError:
        current_idx = 0
    
    def on_profile_change():
        """Callback when profile selection changes"""
        selected_id = st.session_state.get('profile_select_id', 'new')
        
        if selected_id == 'new':
            # Clear form for new profile
            st.session_state['current_profile_id'] = None
            st.session_state['input_name'] = "某人"
            st.session_state['input_gender'] = "男"
            st.session_state['input_date'] = dt(1990, 1, 1)
            st.session_state['input_time'] = 12
            st.session_state['input_minute'] = 0
            st.session_state['unified_geo_city'] = "None"
            st.session_state['input_longitude'] = 116.46
        else:
            # Load selected profile
            profile = next((p for p in all_profiles if p.get('id') == selected_id), None)
            if profile:
                st.session_state['current_profile_id'] = profile.get('id')
                st.session_state['input_name'] = profile.get('name', '某人')
                st.session_state['input_gender'] = profile.get('gender', '男')
                try:
                    st.session_state['input_date'] = dt(
                        int(profile['year']), 
                        int(profile['month']), 
                        int(profile['day'])
                    )
                except:
                    st.session_state['input_date'] = dt(1990, 1, 1)
                st.session_state['input_time'] = int(profile.get('hour', 12))
                st.session_state['input_minute'] = int(profile.get('minute', 0))
                st.session_state['unified_geo_city'] = profile.get('city', 'None') or 'None'
                st.session_state['input_longitude'] = float(profile.get('longitude', 116.46) or 116.46)
    
    selected_display = st.selectbox(
        "选择档案 (Select Profile)",
        options=option_list,
        format_func=lambda x: profile_options.get(x, x),
        index=current_idx,
        key="profile_select_id",
        on_change=on_profile_change
    )

    # --- Save / Delete Actions ---
    col_save, col_del = st.columns([1, 1])
    
    with col_save:
        if st.button("💾 保存当前", key="btn_save", width='stretch'):
            _do_save_profile(pm)
    
    with col_del:
        current_profile_id = st.session_state.get('current_profile_id')
        if current_profile_id and st.button("🗑️ 删除选中", key="btn_del", width='stretch'):
            ok, msg = pm.delete_profile(current_profile_id)
            if ok:
                st.success("已删除")
                st.session_state['current_profile_id'] = None
                st.session_state['_pending_profile_select'] = 'new'
                time.sleep(0.5)
                st.rerun()


def _do_save_profile(pm):
    """Handle profile save action"""
    # Get values from session state
    s_name = st.session_state.get('input_name', '').strip()
    s_gender = st.session_state.get('input_gender', '男')
    s_date = st.session_state.get('input_date', dt(1990, 1, 1))
    s_time = st.session_state.get('input_time', 12)
    s_minute = st.session_state.get('input_minute', 0)
    s_city = st.session_state.get('unified_geo_city', None)
    s_longitude = st.session_state.get('input_longitude', 116.46)
    
    # Get current profile ID (None for new profile)
    current_profile_id = st.session_state.get('current_profile_id')
    
    if not s_name or s_name == "某人":
        st.error("请输入有效姓名")
        return
    
    # Save profile
    ok, msg = pm.save_profile(
        profile_id=current_profile_id,
        name=s_name,
        gender=s_gender,
        year=s_date.year,
        month=s_date.month,
        day=s_date.day,
        hour=s_time,
        minute=s_minute,
        city=s_city if s_city and s_city != "None" else None,
        longitude=s_longitude
    )
    
    if ok:
        # msg contains the profile ID (returned from save_profile)
        saved_profile_id = msg
        st.session_state['current_profile_id'] = saved_profile_id
        # Use pending state to update selection on next rerun
        st.session_state['_pending_profile_select'] = saved_profile_id
        
        st.success(f"已保存: {s_name}")
        time.sleep(0.5)
        st.rerun()
    else:
        st.error(f"保存失败: {msg}")


def _render_bazi_quick_test():
    """
    Quick Bazi Test - Single input field with auto-parsing
    User inputs complete 8-character bazi string: "乙未丙戌壬戌辛亥"
    System auto-parses into 4 pillars
    """
    st.caption("⚡ 快速测试：输入完整八字（8个字），系统自动识别四柱")
    
    # Quick Bazi Input
    bazi_str = st.text_input(
        "八字输入 (8字)", 
        value="", 
        placeholder="例: 乙未丙戌壬戌辛亥",
        key="quick_bazi_input"
    )
    
    gender_quick = st.radio("性别", ["男", "女"], horizontal=True, key="quick_gender")
    
    if st.button("⚡ 快速分析", key="btn_quick_analyze"):
        if len(bazi_str) == 8:
            # Parse into pillars
            pillars = {
                'year': bazi_str[0:2],
                'month': bazi_str[2:4],
                'day': bazi_str[4:6],
                'hour': bazi_str[6:8]
            }
            
            # Store in session state for analysis
            st.session_state['quick_bazi_pillars'] = pillars
            st.session_state['quick_bazi_gender'] = gender_quick
            
            # Try to reverse-calculate date
            date_result = _reverse_calculate_date(pillars)
            
            if date_result:
                st.success(f"✅ 推算出生日期: {date_result}")
                # Sync to main input form
                try:
                    parts = date_result.split(' ')
                    date_parts = parts[0].split('-')
                    time_parts = parts[1].split(':')
                    
                    st.session_state['input_date'] = dt(
                        int(date_parts[0]), 
                        int(date_parts[1]), 
                        int(date_parts[2])
                    )
                    st.session_state['input_time'] = int(time_parts[0])
                    st.session_state['input_gender'] = gender_quick
                    st.session_state['input_name'] = f"测试_{bazi_str[:4]}"
                except:
                    pass
            else:
                st.warning("⚠️ 无法推算日期，请手动输入")
            
            # Display parsed pillars
            st.markdown("**解析结果:**")
            cols = st.columns(4)
            labels = ["年柱", "月柱", "日柱", "时柱"]
            pillar_keys = ['year', 'month', 'day', 'hour']
            for i, (label, key) in enumerate(zip(labels, pillar_keys)):
                with cols[i]:
                    st.metric(label, pillars[key])
        else:
            st.error(f"请输入8个字符的八字，当前: {len(bazi_str)}个字")


def _reverse_calculate_date(pillars, start_year=1950, end_year=2030):
    """
    Reverse calculate date from Bazi pillars
    """
    try:
        from core.bazi_reverse_calculator import BaziReverseCalculator
        
        calculator = BaziReverseCalculator(year_range=(start_year, end_year))
        result = calculator.reverse_calculate(
            pillars,
            precision='high',
            consider_lichun=True
        )
        
        if result and result.get('birth_date'):
            birth_date = result['birth_date']
            if isinstance(birth_date, dt):
                return f"{birth_date.year}-{birth_date.month}-{birth_date.day} {birth_date.hour}:00"
    except Exception as e:
        pass
    
    # Fallback to legacy method
    return _reverse_calculate_date_legacy(pillars, start_year, end_year)


def _reverse_calculate_date_legacy(pillars, start_year=1950, end_year=2030):
    """Legacy reverse calculation method"""
    import datetime
    
    tg_y = pillars.get('year', '')
    tg_m = pillars.get('month', '')
    tg_d = pillars.get('day', '')
    tg_h = pillars.get('hour', '')
    
    for y in range(start_year, end_year + 1):
        try:
            test_solar = Solar.fromYmd(y, 6, 15)
            lunar = test_solar.getLunar()
            curr_y_gz = lunar.getYearInGanZhi()
            
            if curr_y_gz == tg_y:
                start_d = datetime.date(y, 1, 15)
                end_d = datetime.date(y + 1, 2, 15)
                
                curr = start_d
                while curr < end_d:
                    try:
                        s = Solar.fromYmd(curr.year, curr.month, curr.day)
                        l = s.getLunar()
                        
                        if l.getYearInGanZhiExact() == tg_y:
                            if l.getMonthInGanZhiExact() == tg_m:
                                if l.getDayInGanZhiExact() == tg_d:
                                    for h in range(0, 24, 2):
                                        sh = Solar.fromYmdHms(curr.year, curr.month, curr.day, h, 0, 0)
                                        lh = sh.getLunar()
                                        if lh.getTimeInGanZhi() == tg_h:
                                            return f"{sh.getYear()}-{sh.getMonth()}-{sh.getDay()} {sh.getHour()}:00"
                    except:
                        pass
                    
                    curr += datetime.timedelta(days=1)
        except:
            pass
    
    return None
