import streamlit as st
import plotly.graph_objects as go
import numpy as np
from typing import Dict
from core.trinity.core.physics.wave_laws import WaveState

class Oscilloscope:
    """
    Quantum Trinity V14.0 Oscilloscope
    ==================================
    Visualizes the Wave Function of the Five Elements in the complex plane.
    """
    
    COLORS = {
        'Wood': '#4ade80',  # Green
        'Fire': '#f87171',  # Red
        'Earth': '#fdba74', # Orange
        'Metal': '#94a3b8', # Metalgrey
        'Water': '#38bdf8'  # Blue
    }
    
    @staticmethod
    def render(waves: Dict[str, WaveState]):
        """
        Renders the Phasor Diagram (Polar Plot).
        
        Args:
            waves: Dictionary mapping Element Name -> WaveState (Amplitude, Phase)
        """
        fig = go.Figure()
        
        # 1. Plot Vectors (Phasors)
        for elem, wave in waves.items():
            if wave.amplitude <= 0.01: continue
            
            # Convert polar to degrees for Plotly
            r = wave.amplitude
            theta_deg = np.degrees(wave.phase) % 360
            
            color = Oscilloscope.COLORS.get(elem, '#cccccc')
            
            # Vector Line
            fig.add_trace(go.Scatterpolar(
                r=[0, r],
                theta=[0, theta_deg],
                mode='lines+markers',
                name=elem,
                line=dict(color=color, width=3),
                marker=dict(size=8, symbol='circle')
            ))
            
            # Waveform Envelope (Concept) - Optional, simplified for now to just Phasors
            
        # 2. Layout Styling
        fig.update_layout(
            title="Quantum Phasor Field (V14.7)",
            font=dict(size=12, color="#e2e8f0"),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 10], showline=False, gridcolor='rgba(255,255,255,0.1)'),
                angularaxis=dict(
                    tickmode='array',
                    tickvals=[0, 72, 144, 216, 288],
                    ticktext=['Wood (0°)', 'Fire (72°)', 'Earth (144°)', 'Metal (216°)', 'Water (288°)'],
                    gridcolor='rgba(255,255,255,0.1)',
                    linecolor='rgba(255,255,255,0.1)'
                ),
                bgcolor='rgba(0,0,0,0.1)'
            ),
            showlegend=True,
            legend=dict(orientation="h", x=0.1, y=-0.2),
            margin=dict(l=40, r=40, t=40, b=40)
        )
        
        st.plotly_chart(fig, width='stretch')

    @staticmethod
    def render_interference_monitor(interactions: list):
        """
        Renders a bar chart of constructive vs destructive interference events.
        """
        if not interactions:
            st.info("No active interference patterns detected.")
            return

        # Categorize
        # Assuming interactions are strings or dicts. V14 logic returns dicts or strings depending on version.
        # Let's assume strings for now based on 'match_logic' output in debug script.
        
        categories = {'Constructive': 0, 'Destructive': 0, 'Neutral': 0}
        
        for i in interactions:
            # Simple heuristic parsing of the rule string
            s = str(i).lower()
            if "clash" in s or "harm" in s or "punish" in s or "control" in s:
                categories['Destructive'] += 1
            elif "combine" in s or "generate" in s or "assist" in s:
                 categories['Constructive'] += 1
            else:
                categories['Neutral'] += 1
                
        # Bar Chart
        fig = go.Figure([go.Bar(
            x=list(categories.keys()),
            y=list(categories.values()),
            marker_color=['#4ade80', '#ef4444', '#94a3b8']
        )])
        
        fig.update_layout(
            title="Interference Spectrum",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0'),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
            height=200,
            margin=dict(t=30, b=20, l=20, r=20)
        )
        st.plotly_chart(fig, width='stretch')
