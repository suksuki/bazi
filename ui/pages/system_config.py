import streamlit as st
import ollama

def render_system_config(config_manager):
    """
    Renders the System Config page.
    Args:
        config_manager: Instance of ConfigManager.
    """
    st.header("⚙️ 系统控制台 (System Console)")
    
    # ==================== 学习任务配置 ====================
    st.subheader("📚 学习任务引擎 (Learning Engine)")
    
    col_learn_1, col_learn_2 = st.columns([1, 1])
    
    with col_learn_1:
        # 并发任务数设置
        cur_limit = int(config_manager.get('max_concurrent_jobs', 3))
        new_limit = st.number_input(
            "⚡ 最大并发任务数", 
            min_value=1, 
            max_value=10, 
            value=cur_limit,
            help="同时处理的学习任务数量。建议3-5个，过高可能导致系统资源紧张"
        )
        if new_limit != cur_limit:
            config_manager.save_config('max_concurrent_jobs', new_limit)
            st.success(f"✅ 并发数已更新为 {new_limit}，新任务将立即生效！")
    
    with col_learn_2:
        # 字幕优先级设置
        subtitle_priority = config_manager.get('subtitle_priority', True)
        new_priority = st.checkbox(
            "💬 优先使用CC字幕",
            value=subtitle_priority,
            help="开启后，优先下载视频字幕，跳过Whisper转录，大幅提升速度"
        )
        if new_priority != subtitle_priority:
            config_manager.save_config('subtitle_priority', new_priority)
            st.success(f"✅ 字幕优先级已{'开启' if new_priority else '关闭'}")
    
    # 字幕语言配置
    with st.expander("🌐 字幕语言优先级", expanded=False):
        st.caption("视频学习时，将按此顺序尝试下载字幕")
        
        default_langs = ['zh-Hans', 'zh-Hant', 'zh-CN', 'zh-TW', 'zh', 'en']
        current_langs = config_manager.get('subtitle_languages', default_langs)
        
        lang_text = st.text_area(
            "语言代码（每行一个）",
            value="\n".join(current_langs),
            height=150,
            help="常用代码: zh-Hans(简中), zh-Hant(繁中), zh(中文), en(英文)"
        )
        
        new_langs = [lang.strip() for lang in lang_text.split('\n') if lang.strip()]
        if new_langs != current_langs:
            config_manager.save_config('subtitle_languages', new_langs)
            st.success(f"✅ 字幕语言优先级已更新: {' → '.join(new_langs[:3])}...")
    
    st.divider()
    
    # ==================== LLM配置 ====================
    st.subheader("🤖 大模型脑核 (LLM Core)")
    col_llm_1, col_llm_2 = st.columns([1, 1])
    
    with col_llm_1:
         ollama_host = st.text_input("Ollama Server URL", value=st.session_state.get('ollama_host', 'http://localhost:11434'))
    
    # Update config
    if ollama_host != st.session_state.get('ollama_host'):
        st.session_state['ollama_host'] = ollama_host
        config_manager.save_config("ollama_host", ollama_host)

    with st.expander("🛠️ 高级连接调试", expanded=True):
        if st.button("📡 测试连接 & 刷新模型列表"):
            # Check availability (We assume ollama library is available as this function is imported when needed)
            try:
                client = ollama.Client(host=ollama_host)
                resp = client.list()
                # extract model names
                models = []
                model_list = resp.models if hasattr(resp, 'models') else resp.get('models', [])
                
                for m in model_list:
                    if hasattr(m, 'model'):
                        models.append(m.model)
                    elif isinstance(m, dict):
                        models.append(m.get('model') or m.get('name'))
                    else:
                        models.append(str(m))
                        
                st.session_state['ollama_models'] = models
                st.success(f"连接成功! 发现 {len(models)} 个模型")
                
                # Save host on success
                config_manager.save_config("ollama_host", ollama_host)
                
            except Exception as e:
                st.error(f"连接失败: {e}")
    
        # Model Selector
        model_options = st.session_state.get('ollama_models', [])
        
        index = 0
        current_selection = st.session_state.get('selected_model_name', '')
        if current_selection and current_selection in model_options:
            index = model_options.index(current_selection)
        
        saved_model = config_manager.get("selected_model_name") # Read for display info

        if model_options:
            selected_model_name = st.selectbox("选择此服务器上的模型", model_options, index=index)
            
            if selected_model_name != st.session_state.get('selected_model_name'):
                st.session_state['selected_model_name'] = selected_model_name
                config_manager.save_config("selected_model_name", selected_model_name)
            
            # Quick Test Button
            if st.button("🟢 验证模型响应 (Test Run)"):
                try:
                    with st.spinner("正在发送测试信号..."):
                        client = ollama.Client(host=ollama_host)
                        res = client.generate(model=selected_model_name, prompt="Say 'Ready' in Chinese", stream=False)
                        st.success(f"模型响应正常: {res['response']}")
                except Exception as e:
                    st.error(f"模型无响应: {e}")
        else:
            if saved_model:
                 st.info(f"上次使用的模型: {saved_model} (状态: 未连接)")
            else:
                 st.info("请先测试连接以加载模型列表")

