
import streamlit as st
import plotly.graph_objects as go
import numpy as np

class EnvelopeGauge:
    """
    Phase 21 UI Component: Resonance Envelope Monitor.
    Visualizes the beating envelope and current phase risk.
    """

    @staticmethod
    def render(env: float, freq: float, t: float = 0.0):
        """
        Renders a gauge chart for Envelope (0.0 - 1.0) and a small sparkline of the wave.
        """
        # Determine Color based on Envelope
        if env >= 0.6:
            bar_color = "#40e0d0" # Teal - Deep Sync
        elif env >= 0.2:
            bar_color = "#ffaa00" # Orange - Beating
        else:
            bar_color = "#ff4b4b" # Red - Crisis
            
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = env,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Envelope (Env)"},
            gauge = {
                'axis': {'range': [0, 1], 'tickwidth': 1, 'tickcolor': "white"},
                'bar': {'color': bar_color},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 2,
                'bordercolor': "#333",
                'steps': [
                    {'range': [0, 0.2], 'color': 'rgba(255, 75, 75, 0.3)'},
                    {'range': [0.2, 0.6], 'color': 'rgba(255, 170, 0, 0.3)'},
                    {'range': [0.6, 1.0], 'color': 'rgba(64, 224, 208, 0.3)'}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': env
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
        
        if env < 0.2:
            st.error("⚠️ PHASE CRISIS DETECTED! Potential collapse in this time vector.")
        elif env < 0.6:
            st.warning("🌀 Beating Mode active. System energy is oscillating.")

        # Sparkline simulation
        t_range = np.linspace(t-10, t+10, 100)
        env_trace = np.abs(np.cos(freq * t_range / 2.0))
        
        fig_trace = go.Figure()
        fig_trace.add_trace(go.Scatter(x=t_range, y=env_trace, line=dict(color='#40e0d0', width=1)))
        fig_trace.add_trace(go.Scatter(x=[t], y=[env], mode='markers', marker=dict(color='white', size=10)))
        
        fig_trace.update_layout(
            title="Spacetime Waveform (Envelope Trace)",
            height=150,
            showlegend=False,
            paper_bgcolor = "rgba(0,0,0,0)",
            plot_bgcolor = "rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, range=[0, 1.1]),
            margin = {'t': 30, 'b': 10, 'l': 10, 'r': 10}
        )
        st.plotly_chart(fig_trace, use_container_width=True)
