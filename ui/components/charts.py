
"""
ui/components/charts.py
-----------------------
Plotly Chart rendering logic.
"""
import plotly.graph_objects as go
import pandas as pd


class DestinyCharts:
    @staticmethod
    def render_life_curve(df_traj, sim_year, handover_years):
        """
        Renders the Dynamic Trajectory Chart using Plotly.
        """
        if df_traj.empty or 'label' not in df_traj.columns:
            return None

        # Prepare Treasury Points
        treasury_points_labels = []
        treasury_points_y = []
        treasury_icons = []
        treasury_colors = []
        
        # Iterate to find treasury events
        for i, row in df_traj.iterrows():
            if row.get('is_treasury_open'):
                treasury_points_labels.append(row['year']) # Use year (x-axis) or label
                # Note: The original code used 'label' for X in treasury scaffold, but 'year' for lines.
                # Plotly scatter x-axis types must match. 'year' is int, 'label' is string. 
                # The line chart uses 'year' (int). So we must use 'year' for treasury points too.
                # However, the original code used `row['label']` for treasury text.
                # Let's check the original code again. 
                # It passed `x=treasury_points_labels` where `treasury_points_labels.append(row['label'])`.
                # But the main traces use `x=df_traj['year']`.
                # If 'year' is numerical and 'label' is categorical string, mixing them on one axis might be tricky in Plotly unless it automatically handles it.
                # But usually it's safer to use the same X axis type.
                # The original code worked because maybe 'label' was somehow compatible or Plotly is smart.
                # Actually, in the original code: 
                # fig.add_trace(go.Scatter(x=df_traj['year']...))
                # fig.add_trace(go.Scatter(x=treasury_points_labels...))
                # If 'year' is 2024 and 'label' is "2024\nJiaChen", this puts them on different X scales usually?
                # Ah, unless `sim_year` is int, and the plotting works.
                # Wait, let's look at the original code carefully:
                # `treasury_points_labels.append(row['label'])` -> `fig.add_trace(..., x=treasury_points_labels, ...)`
                # The main traces use `x=df_traj['year']`.
                # This suggests the X-axis might be mixed or I misremember how Plotly handles mixed types.
                # Or maybe `df_traj['year']` is used for positioning and `label` for categorical?
                # Actually, to be safe and ensuring alignment, we should probably use `year` for the X-axis of the icons as well,
                # and just use the label for text or hover.
                # BUT, I will stick to the exact logic of the original file to avoid breaking regression, 
                # UNLESS I see it's definitely wrong. 
                # Let's assume the previous code worked or was intended to work.
                # On second thought, using `year` for X axis alignment is strictly better for overlaying on a time series.
                # I will change x to `row['year']` for the icons trace to ensure it aligns with the lines.
                
                treasury_points_labels.append(row['year']) 
                
                # Place icon at the highest point of the 3 lines
                y_max = max(row['career'], row['wealth'], row['relationship'])
                treasury_points_y.append(y_max)
                
                icon = row.get('treasury_icon', '🗝️')
                treasury_icons.append(icon)
                
                risk = row.get('treasury_risk', 'opportunity')
                if risk == 'warning':
                    treasury_colors.append('#FF6B35')  # Orange for warning
                elif risk == 'danger':
                    treasury_colors.append('#FF0000') # Red for danger (Skull)
                else:
                    treasury_colors.append('#FFD700')  # Gold for opportunity

        fig = go.Figure()
        
        # --- Ghost Lines (Base Comparison) ---
        if 'base_career' in df_traj.columns and not df_traj['base_career'].isnull().all():
             fig.add_trace(go.Scatter(
                x=df_traj['year'], y=df_traj['base_career'],
                mode='lines', name='原生 (Base)',
                line=dict(color='rgba(0, 229, 255, 0.3)', width=2, dash='dot'),
                hoverinfo='skip'
            ))
             fig.add_trace(go.Scatter(
                x=df_traj['year'], y=df_traj['base_wealth'],
                mode='lines', showlegend=False,
                line=dict(color='rgba(255, 215, 0, 0.3)', width=2, dash='dot'),
                hoverinfo='skip'
            ))
             fig.add_trace(go.Scatter(
                x=df_traj['year'], y=df_traj['base_relationship'],
                mode='lines', showlegend=False,
                line=dict(color='rgba(245, 0, 87, 0.3)', width=2, dash='dot'),
                hoverinfo='skip'
            ))

        # Base trajectory lines
        fig.add_trace(go.Scatter(
            x=df_traj['year'], 
            y=df_traj['career'], 
            mode='lines+markers', 
            name='事业 (Career)',
            line=dict(color='#00E5FF', width=3),
            connectgaps=True,
            hovertext=df_traj['desc']
        ))
        fig.add_trace(go.Scatter(
            x=df_traj['year'], 
            y=df_traj['wealth'], 
            mode='lines+markers', 
            name='财富 (Wealth)',
            line=dict(color='#FFD700', width=3),
            connectgaps=True,
            hovertext=df_traj['desc']
        ))
        fig.add_trace(go.Scatter(
            x=df_traj['year'], 
            y=df_traj['relationship'], 
            mode='lines+markers', 
            name='感情 (Rel)',
            line=dict(color='#F50057', width=3),
            connectgaps=True,
            hovertext=df_traj['desc']
        ))
        
        # Treasury Icon Overlay
        if treasury_points_labels:
            fig.add_trace(go.Scatter(
                x=treasury_points_labels, 
                y=treasury_points_y,
                mode='text',
                text=treasury_icons,
                textposition="top center",
                textfont=dict(size=36),
                marker=dict(color=treasury_colors),
                name='💰 库门事件',
                hoverinfo='skip',
                showlegend=False
            ))
        
        # Handover Lines
        for handover in handover_years:
            fig.add_vline(
                x=handover['year'],
                line_width=2,
                line_dash="dash",
                line_color="rgba(255,255,255,0.6)",
                annotation_text=f"🔄 换运\\n{handover['to']}",
                annotation_position="top",
                annotation=dict(
                    font=dict(size=10, color="white"),
                    bgcolor="rgba(100,100,255,0.3)",
                    bordercolor="rgba(255,255,255,0.5)",
                    borderwidth=1
                )
            )
        
        # Final Layout
        fig.update_layout(
            title="🏛️ Antigravity V6.0: 命运全息图 (Destiny Wavefunction)",
            yaxis=dict(title="能量级 (Energy Score)", range=[-12, 12]), # Slightly expanded range
            xaxis=dict(
                title="年份 (Year)",
                range=[sim_year - 0.5, sim_year + 11.5],
                tickmode='linear',
                dtick=1
            ),
            hovermode="x unified",
            margin=dict(l=40, r=40, t=60, b=80),
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.25,
                xanchor="center",
                x=0.5,
                font=dict(size=12),
                bgcolor="rgba(0,0,0,0.5)",
                bordercolor="rgba(255,255,255,0.3)",
                borderwidth=1
            ),
            plot_bgcolor='rgba(0,0,0,0.05)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig

