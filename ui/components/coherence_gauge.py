
import streamlit as st
import plotly.graph_objects as go

class CoherenceGauge:
    """
    Phase 18 UI Component: Coherence (Eta) Visualization.
    Visualizes the structural integrity of a Bazi combination.
    """

    @staticmethod
    def render(eta: float, stability_desc: str = "", binding_energy: float = 0.0):
        """
        Renders a gauge chart for Eta (0.0 - 1.0) and a metric for Binding Energy.
        """
        # Determine Color based on Eta
        if eta >= 0.8:
            bar_color = "#00ff00" # Green - Solid
        elif eta >= 0.4:
            bar_color = "#ffaa00" # Amber - Unstable
        else:
            bar_color = "#ff0000" # Red - Collapsed/Weak
            
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = eta,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Coherence (η)"},
            gauge = {
                'axis': {'range': [0, 1], 'tickwidth': 1, 'tickcolor': "white"},
                'bar': {'color': bar_color},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 2,
                'bordercolor': "#333",
                'steps': [
                    {'range': [0, 0.3], 'color': 'rgba(255, 0, 0, 0.3)'},
                    {'range': [0.3, 0.7], 'color': 'rgba(255, 170, 0, 0.3)'},
                    {'range': [0.7, 1.0], 'color': 'rgba(0, 255, 0, 0.3)'}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': eta
                }
            }
        ))
        
        fig.update_layout(
            paper_bgcolor = "rgba(0,0,0,0)",
            font = {'color': "white", 'family': "Arial"},
            margin = {'t': 40, 'b': 20, 'l': 20, 'r': 20},
            height = 250
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Stability Description
        st.markdown(f"**Stability Status**: {stability_desc}")
        st.progress(min(1.0, max(0.0, eta)))
        
        # Binding Energy Metric
        st.metric("Binding Energy (E_bind)", f"{binding_energy:.2f}", 
                  help="Energy required to break this structure.")

    @staticmethod
    def render_energy_breakdown(native: float, transformed: float):
        """
        Renders a bar chart comparing Native Logic vs Transformed Logic energy.
        """
        fig = go.Figure(data=[
            go.Bar(name='Native (Original)', x=['Energy'], y=[native], marker_color='#888'),
            go.Bar(name='Transformed (Fused)', x=['Energy'], y=[transformed], marker_color='#00ccff')
        ])
        
        fig.update_layout(
            barmode='stack',
            title="Energy Composition",
            paper_bgcolor = "rgba(0,0,0,0)",
            plot_bgcolor = "rgba(0,0,0,0)",
            font = {'color': "white"},
            height = 200,
            showlegend = True,
            legend = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
