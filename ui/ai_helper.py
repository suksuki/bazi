import streamlit as st
import ollama

@st.cache_data(show_spinner=False)
def get_ai_advice(profile_id, chart_str, strength_str, reactions_str, host, model_name):
    """
    Cached AI Advice. 
    Keys on profile_id (or distinctive chart features) to avoid re-running 
    when user toggles UI irrelevant to the chart itself.
    """
    if not host or not model_name:
        return "请先在【系统配置】中设置 Ollama 模型"
        
    try:
        client = ollama.Client(host=host, timeout=60) # Increased Timeout to 60s
        prompt = f"""
        你是八字专家。
        八字结构：{chart_str}
        五行强弱: {strength_str}
        主要反应: {reactions_str}
        
        请用**极简短**的语言（3个要点），直击痛点，指出此人当下的核心机遇或风险。
        不要废话，直接给干货。
        """
        resp = client.generate(model=model_name, prompt=prompt, stream=False)
        if 'response' in resp:
             return resp['response']
        return "AI 未返回有效内容"
    except Exception as e:
        return f"Error: {e}"
