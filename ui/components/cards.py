
import streamlit as st
import streamlit.components.v1 as components
from .styles import get_theme, get_nature_color, get_bazi_table_css
from core.interactions import get_stem_interaction, get_branch_interaction

class DestinyCards:
    
    @staticmethod
    def render_narrative_card(event):
        """
        Renders a single narrative card based on the event payload.
        Uses Quantum Glassmorphism styles.
        """
        ctype = event.get('card_type', 'default')
        
        # Map types to CSS classes and icons
        config = {
            "mountain_alliance": {"css": "card-mountain", "icon": "⛰️", "icon_css": "icon-mountain"},
            "penalty_cap": {"css": "card-shield", "icon": "🛡️", "icon_css": "icon-shield"},
            "mediation": {"css": "card-flow", "icon": "🌊", "icon_css": "icon-flow"},
            "pressure": {"css": "card-danger", "icon": "⚠️", "icon_css": ""},
            "control": {"css": "card-flow", "icon": "⚡", "icon_css": "icon-flow"}, # Re-use flow for control
            "default": {"css": "", "icon": "📜", "icon_css": ""}
        }
        
        cfg = config.get(ctype, config.get(event.get('type'), config['default'])) # Fallback to 'type' key if 'card_type' missing
        
        # Generate HTML
        html = f"""
        <div class="narrative-card {cfg['css']}">
            <div style="display: flex; align-items: start; gap: 16px;">
                <div class="{cfg['icon_css']}">{cfg['icon']}</div>
                <div style="flex-grow: 1;">
                    <div class="card-title">{event.get('title', 'Unknown Event')}</div>
                    <div class="card-subtitle">{event.get('desc', '')}</div>
                    <div class="card-impact">{event.get('score_delta', '')}</div>
                </div>
            </div>
            <!-- Visualization Placeholder -->
            <div style="position: absolute; right: 10px; top: 10px; opacity: 0.1;">
                <span style="font-size: 60px;">{cfg['icon']}</span>
            </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

    @staticmethod
    def render_bazi_table(chart, selected_yun, current_gan_zhi, flux_data, interactions_context=None):
        """
        Renders the Four Pillars table.
        
        Args:
            chart: Dictionary containing bazi chart data (year, month, day, hour).
            selected_yun: Dictionary containing Da Yun info.
            current_gan_zhi: String for current Liu Nian (e.g., '甲辰').
            flux_data: Dictionary of energy/flux data (used heavily for scoring).
        """
        # Prepare Data
        pillars = ['year', 'month', 'day', 'hour']
        labels = ["年柱 (Year)", "月柱 (Month)", "日柱 (Day)", "时柱 (Hour)"]
        
        # Helper for interactions
        def fmt_int(txt):
            if not txt: return ""
            color = "#AAA"
            icon = "🔗"
            if "冲" in txt: 
                color = "#FF4500" # Red/Orange for Clash
                icon = "💥"
            elif "刑" in txt: 
                color = "#FFD700" # Gold for Punishment
                icon = "⚡"
            elif "害" in txt: 
                color = "#FF69B4" # Pink for Harm
                icon = "💔"
            elif "合" in txt: 
                color = "#00FF00" # Green for Combine
                icon = "🤝"
                
            return f"<div style='color:{color}; font-size:0.45em; border:1px solid {color}; border-radius:4px; padding:1px; margin-top:2px; display:inline-block;'>{icon} {txt}</div>"

        # Extract Chart Data
        y_s = chart.get('year',{}).get('stem','?')
        y_b = chart.get('year',{}).get('branch','?')
        m_s = chart.get('month',{}).get('stem','?')
        m_b = chart.get('month',{}).get('branch','?')
        d_s = chart.get('day',{}).get('stem','?')
        d_b = chart.get('day',{}).get('branch','?')
        h_s = chart.get('hour',{}).get('stem','?')
        h_b = chart.get('hour',{}).get('branch','?')
        
        l_s = selected_yun['gan_zhi'][0] if selected_yun else '?'
        l_b = selected_yun['gan_zhi'][1] if selected_yun else '?'
        
        n_s = current_gan_zhi[0] if current_gan_zhi else '?'
        n_b = current_gan_zhi[1] if current_gan_zhi else '?'
        
        # Interactions relative to Day Pillar (Day Master / Day Branch)
        i_y_s = fmt_int(get_stem_interaction(y_s, d_s))
        i_m_s = fmt_int(get_stem_interaction(m_s, d_s))
        i_h_s = fmt_int(get_stem_interaction(h_s, d_s))
        i_l_s = fmt_int(get_stem_interaction(l_s, d_s))
        i_n_s = fmt_int(get_stem_interaction(n_s, d_s))
        
        i_y_b = fmt_int(get_branch_interaction(y_b, d_b))
        i_m_b = fmt_int(get_branch_interaction(m_b, d_b))
        i_h_b = fmt_int(get_branch_interaction(h_b, d_b))
        i_l_b = fmt_int(get_branch_interaction(l_b, d_b))
        i_n_b = fmt_int(get_branch_interaction(n_b, d_b))

        # Capture Pillar Energies
        # We need to replicate the 'pe' logic from dashboard
        # This requires access to flux_engine.particles which is tricky if we only pass flux_data (dict)
        # But flux_data usually aggregates by Ten Gods.
        # Wait, the dashboard code iterates `flux_engine.particles`.
        # So we might need to pass `flux_engine` or pass the `pe` list directly.
        # To keep it simple, let's pass `pe_list` (pillar energies) as an argument or calculate it if we pass flux_engine.
        # Passing `pe_list` is cleaner View logic.
        
        pass

    @staticmethod
    def render_bazi_table_with_engine(chart, selected_yun, current_gan_zhi, pe_list, scale=0.08, wang_shuai_str=""):
        """
        Renders the Four Pillars table using pre-calculated pillar energies.
        
        V9.6 Architecture Fix: Changed from accepting flux_engine to accepting pe_list
        to maintain View layer purity. All calculation logic should be in Controller.
        
        Args:
            chart: Bazi chart dictionary
            selected_yun: Selected Da Yun dict
            current_gan_zhi: Current Liu Nian GanZhi string
            pe_list: Pre-calculated pillar energies list [year_stem, year_branch, ..., hour_branch]
            scale: Scaling factor (kept for compatibility, but pe_list should already be scaled)
            wang_shuai_str: Wang/Shuai strength string
        """
        # Use provided pillar energies (already calculated by Controller)
        pe = pe_list if pe_list and len(pe_list) == 8 else [0.0] * 8
        
        # Extract Chart Data (Repeated logic, but cleaner to have it all here)
        y_s = chart.get('year',{}).get('stem','?')
        y_b = chart.get('year',{}).get('branch','?')
        m_s = chart.get('month',{}).get('stem','?')
        m_b = chart.get('month',{}).get('branch','?')
        d_s = chart.get('day',{}).get('stem','?')
        d_b = chart.get('day',{}).get('branch','?')
        h_s = chart.get('hour',{}).get('stem','?')
        h_b = chart.get('hour',{}).get('branch','?')
        
        l_s = selected_yun['gan_zhi'][0] if selected_yun else '?'
        l_b = selected_yun['gan_zhi'][1] if selected_yun else '?'
        
        n_s = current_gan_zhi[0] if current_gan_zhi else '?'
        n_b = current_gan_zhi[1] if current_gan_zhi else '?'
        
        # Helper for interactions
        def fmt_int(txt):
            if not txt: return ""
            color = "#AAA"
            icon = "🔗"
            if "冲" in txt: 
                color = "#FF4500" # Red/Orange for Clash
                icon = "💥"
            elif "刑" in txt: 
                color = "#FFD700" # Gold for Punishment
                icon = "⚡"
            elif "害" in txt: 
                color = "#FF69B4" # Pink for Harm
                icon = "💔"
            elif "合" in txt: 
                color = "#00FF00" # Green for Combine
                icon = "🤝"
            return f"<div style='color:{color}; font-size:0.45em; border:1px solid {color}; border-radius:4px; padding:1px; margin-top:2px; display:inline-block;'>{icon} {txt}</div>"

        # Interactions relative to Day Pillar (Day Master / Day Branch)
        i_y_s = fmt_int(get_stem_interaction(y_s, d_s))
        i_m_s = fmt_int(get_stem_interaction(m_s, d_s))
        i_h_s = fmt_int(get_stem_interaction(h_s, d_s))
        i_l_s = fmt_int(get_stem_interaction(l_s, d_s))
        i_n_s = fmt_int(get_stem_interaction(n_s, d_s))
        
        i_y_b = fmt_int(get_branch_interaction(y_b, d_b))
        i_m_b = fmt_int(get_branch_interaction(m_b, d_b))
        i_h_b = fmt_int(get_branch_interaction(h_b, d_b))
        i_l_b = fmt_int(get_branch_interaction(l_b, d_b))
        i_n_b = fmt_int(get_branch_interaction(n_b, d_b))

        # 用 components.html 渲染，避免部分环境下 markdown 把 HTML 当纯文本显示
        table_body = f"""
        <div class="bazi-box">
            <table class="bazi-table">
                <tr>
                    <td><div class="bazi-header h-anim-year">🏰 年柱</div></td>
                    <td><div class="bazi-header h-anim-month">🍂 月柱</div></td>
                    <td><div class="bazi-header h-anim-day">👑 日柱</div></td>
                    <td><div class="bazi-header h-anim-hour">⏳ 时柱</div></td>
                    <td style="width: 20px;"></td>
                    <td><div class="bazi-header h-anim-dayun">🛣️ 大运</div></td>
                    <td><div class="bazi-header h-anim-liunian">🌊 流年</div></td>
                </tr>
                <tr>
                    <td class="pillar-cell">
                        <div class="stem" style="color: {get_nature_color(y_s)}">{y_s}</div>
                        <div class="branch" style="color: {get_nature_color(y_b)}">{y_b}</div>
                        <div class="energy-val">{pe[0] + pe[1]:.1f}</div>
                        <div class="int-container">{i_y_s}{i_y_b}</div>
                    </td>
                    <td class="pillar-cell">
                        <div class="stem" style="color: {get_nature_color(m_s)}">{m_s}</div>
                        <div class="branch" style="color: {get_nature_color(m_b)}">{m_b}</div>
                        <div class="energy-val">{pe[2] + pe[3]:.1f}</div>
                        <div class="int-container">{i_m_s}{i_m_b}</div>
                    </td>
                    <td class="pillar-cell dm-glow">
                        <div class="stem day-master" style="color: {get_nature_color(d_s)}">{d_s}</div>
                        <div class="branch day-master" style="color: {get_nature_color(d_b)}">{d_b}</div>
                        <div class="energy-val" style="color: #ffd700;">{pe[4] + pe[5]:.1f}</div>
                        <div class="int-container" style="color: #ffd700; font-size: 0.6rem;">✦ 命主 ✦</div>
                    </td>
                    <td class="pillar-cell">
                        <div class="stem" style="color: {get_nature_color(h_s)}">{h_s}</div>
                        <div class="branch" style="color: {get_nature_color(h_b)}">{h_b}</div>
                        <div class="energy-val">{pe[6] + pe[7]:.1f}</div>
                        <div class="int-container">{i_h_s}{i_h_b}</div>
                    </td>
                    <td></td>
                    <td class="pillar-cell" style="opacity: 0.9;">
                        <div class="stem" style="color: {get_nature_color(l_s)}">{l_s}</div>
                        <div class="branch" style="color: {get_nature_color(l_b)}">{l_b}</div>
                        <div class="energy-val">-</div>
                        <div class="int-container">{i_l_s}{i_l_b}</div>
                    </td>
                    <td class="pillar-cell" style="opacity: 0.9; border-color: rgba(64, 224, 208, 0.3);">
                        <div class="stem" style="color: {get_nature_color(n_s)}">{n_s}</div>
                        <div class="branch" style="color: {get_nature_color(n_b)}">{n_b}</div>
                        <div class="energy-val">-</div>
                        <div class="int-container">{i_n_s}{i_n_b}</div>
                    </td>
                </tr>
            </table>
            <div style="margin-top: 10px; font-size: 0.9em; color: #AAA;">
                旺衰判定: <span style="color: #FFF; font-weight: bold;">{wang_shuai_str}</span>
                <br>
                <span style="font-size: 0.8em; color: #666;">提示：🔗合 💥冲 ⚡刑 💔害 (相对于日柱)</span>
            </div>
        </div>
        """
        full_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">{get_bazi_table_css()}</head><body>{table_body}</body></html>"""
        components.html(full_html, height=420, scrolling=False)

    @staticmethod
    def render_ten_gods_metrics(dg, scale=0.08):
        """
        Renders the Ten Gods energy distribution metrics.
        """
        st.subheader("1.5. 十神能量分布 (Ten Gods Stats)")
        
        ten_gods_meta = {
            "BiJian":    {"name": "比肩", "icon": "🤝", "desc": "坚定的盟友", "tag": "意志"},
            "JieCai":    {"name": "劫财", "icon": "🐺", "desc": "敏锐的猎手", "tag": "竞争"},
            "ShiShen":   {"name": "食神", "icon": "🎨", "desc": "优雅艺术家", "tag": "才华"},
            "ShangGuan": {"name": "伤官", "icon": "🎤", "desc": "叛逆演说家", "tag": "创新"},
            "PianCai":   {"name": "偏财", "icon": "💸", "desc": "慷慨冒险家", "tag": "机遇"},
            "ZhengCai":  {"name": "正财", "icon": "🏰", "desc": "勤勉建设者", "tag": "积累"},
            "QiSha":     {"name": "七杀", "icon": "⚔️", "desc": "无畏的将军", "tag": "魄力"},
            "ZhengGuan": {"name": "正官", "icon": "⚖️", "desc": "公正的法官", "tag": "秩序"},
            "PianYin":   {"name": "偏印", "icon": "🦉", "desc": "孤独的智者", "tag": "洞察"},
            "ZhengYin":  {"name": "正印", "icon": "🛡️", "desc": "仁慈守护者", "tag": "庇护"},
        }
        
        r1c1, r1c2, r1c3, r1c4, r1c5 = st.columns(5)
        r2c1, r2c2, r2c3, r2c4, r2c5 = st.columns(5)
        
        def style_metric(col, key, val):
            meta = ten_gods_meta.get(key, {"name": key, "icon": "?", "desc": "", "tag": ""})
            val_f = float(val)
            
            color = "#B0B0B0" # Silver / Grey
            box_shadow = "0 2px 4px rgba(0,0,0,0.3)"
            
            if val_f > 6: 
                color = "#FF4500" # High Energy Red
                box_shadow = "0 0 8px rgba(255, 69, 0, 0.4)"
            elif val_f > 3: 
                color = "#00E676" # Neon Green
                box_shadow = "0 0 5px rgba(0, 230, 118, 0.3)"
            else:
                color = "#C0C0C0" 
            
            pct = min(val_f * 10, 100) 
            bg_gradient = f"linear-gradient(to top, rgba(255,255,255,0.1) {pct}%, rgba(30,30,30,0.5) {pct}%)"
            
            val_str = f"{val_f:.1f}"
            col.markdown(f"""<div style="text-align: center; border: 1px solid #444; background: {bg_gradient}; padding: 8px 4px; border-radius: 8px; margin-bottom: 8px; box-shadow: {box_shadow}; position: relative; transition: transform 0.2s;">
        <!-- Tag Badge -->
        <div style="position: absolute; top: 4px; right: 4px; font-size: 0.5em; background: #222; color: #888; padding: 1px 4px; border-radius: 4px; opacity: 0.8; border: 1px solid #444;">
            {meta['tag']}
        </div>
        <!-- Icon & Name -->
        <div style="font-size: 0.9em; color: #CCC; margin-bottom: 4px; margin-top: 4px; display: flex; align-items: center; justify-content: center; gap: 4px;">
            <span style="font-size: 1.2em;">{meta['icon']}</span> {meta['name']}
        </div>
        <!-- Value -->
        <div style="font-size: 1.5em; font-weight: 900; color: {color}; margin: -2px 0 2px 0; text-shadow: 0 1px 2px rgba(0,0,0,0.5);">
            {val_str}
        </div>
        <!-- Description -->
        <div style="font-size: 0.65em; color: #999; font-style: italic; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding: 0 2px;">
            {meta['desc']}
        </div>
    </div>""", unsafe_allow_html=True)

        # Column 1: Self
        style_metric(r1c1, "BiJian", dg.get('BiJian', 0) * scale)
        style_metric(r2c1, "JieCai", dg.get('JieCai', 0) * scale)
        
        # Column 2: Output
        style_metric(r1c2, "ShiShen", dg.get('ShiShen', 0) * scale)
        style_metric(r2c2, "ShangGuan", dg.get('ShangGuan', 0) * scale)
        
        # Column 3: Wealth
        style_metric(r1c3, "PianCai", dg.get('PianCai', 0) * scale)
        style_metric(r2c3, "ZhengCai", dg.get('ZhengCai', 0) * scale)
        
        # Column 4: Officer
        style_metric(r1c4, "QiSha", dg.get('QiSha', 0) * scale)
        style_metric(r2c4, "ZhengGuan", dg.get('ZhengGuan', 0) * scale)
        
        # Column 5: Resource
        style_metric(r1c5, "PianYin", dg.get('PianYin', 0) * scale)
        style_metric(r2c5, "ZhengYin", dg.get('ZhengYin', 0) * scale)

    @staticmethod
    def render_quantum_verdicts(results):
        """
        Renders the Quantum Verdicts metrics (Career, Wealth, Rel).
        """
        st.markdown("### ⚛️ 量子断语 (Quantum Verdicts)")
        
        def get_verdict_text(score):
            if score > 6: return "大吉 / 爆发"
            elif score > 2: return "吉 / 上升"
            elif score < -6: return "大凶 / 崩塌"
            elif score < -2: return "凶 / 阻力"
            return "平稳"

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("⚔️ 事业 (Career)", f"{results['career']}", delta=get_verdict_text(results['career']))
        with c2:
            st.metric("💰 财富 (Wealth)", f"{results['wealth']}", delta=get_verdict_text(results['wealth']))
        with c3:
            st.metric("❤️ 感情 (Rel)", f"{results['relationship']}", delta=get_verdict_text(results['relationship']))
