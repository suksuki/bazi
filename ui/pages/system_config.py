import streamlit as st
import ollama

def render_system_config(config_manager):
    """
    Renders the System Config page.
    功能：对话模型/向量模型切换、Ollama 与 ChromaDB 状态检测、古籍 TXT 上传入库。
    Args:
        config_manager: Instance of ConfigManager.
    """
    from ui.components.theme import COLORS, GLASS_STYLE

    # 从配置回填 session_state，便于输入框显示已保存值
    if "ollama_host" not in st.session_state:
        st.session_state["ollama_host"] = config_manager.get("ollama_host", "http://localhost:11434")
    
    st.markdown(f"""
        <div style="{GLASS_STYLE} padding: 25px; margin-bottom: 2rem; border-top: 4px solid {COLORS['mystic_gold']}; text-align: center;">
            <h1 style="color: {COLORS['mystic_gold']}; margin: 0;">⚙️ 系统大阵控制 (System Forge)</h1>
            <p style="color: {COLORS['moon_silver']}; font-style: italic;">调节命运算法的底层参数与链接</p>
        </div>
    """, unsafe_allow_html=True)
    
    # ==================== 学习任务配置 ====================
    st.markdown(f"""
        <div style="{GLASS_STYLE} padding: 15px; margin-bottom: 1rem; border-left: 4px solid {COLORS['teal_mist']};">
            <h3 style="color: {COLORS['mystic_gold']}; margin: 0;">📚 知识炼金 (Learning Engine)</h3>
        </div>
    """, unsafe_allow_html=True)
    
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
    st.markdown(f"""
        <div style="{GLASS_STYLE} padding: 15px; margin-bottom: 1rem; border-left: 4px solid {COLORS['rose_magenta']};">
            <h3 style="color: {COLORS['mystic_gold']}; margin: 0;">🤖 大模型神启 (LLM Core)</h3>
        </div>
    """, unsafe_allow_html=True)
    col_llm_1, col_llm_2 = st.columns([1, 1])
    
    with col_llm_1:
        ollama_host = st.text_input(
            "Ollama Server URL",
            value=st.session_state.get("ollama_host", "http://localhost:11434"),
            help="GB10 本地或远程 Ollama 服务地址",
        )
    if ollama_host != st.session_state.get("ollama_host"):
        st.session_state["ollama_host"] = ollama_host
        config_manager.save_config("ollama_host", ollama_host)

    # ---------- 状态检测：Ollama + ChromaDB/向量库 ----------
    st.markdown("**📡 连接状态**")
    status_col1, status_col2 = st.columns(2)
    with status_col1:
        try:
            client = ollama.Client(host=ollama_host)
            client.list()
            st.success("🟢 Ollama 已连接")
        except Exception as e:
            st.error(f"🔴 Ollama 未连接: {e}")
    with status_col2:
        try:
            from data.vector_db import get_classical_db
            db = get_classical_db()
            n = db.count()
            st.success(f"🟢 古籍向量库就绪（{n} 条）")
        except Exception as e:
            st.warning(f"🟡 向量库未就绪: {e}")

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
            
            if selected_model_name != st.session_state.get("selected_model_name"):
                st.session_state["selected_model_name"] = selected_model_name
                config_manager.save_config("selected_model_name", selected_model_name)
                # 同步到 ai_engine.chat_model，供 AI 判词使用
                ai_cfg = config_manager.get("ai_engine") or {}
                if not isinstance(ai_cfg, dict):
                    ai_cfg = {}
                ai_cfg["chat_model"] = selected_model_name
                config_manager.save_config("ai_engine", ai_cfg)
            
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

    st.divider()

    # ==================== 向量模型 (Embedding) ====================
    st.markdown(f"""
        <div style="{GLASS_STYLE} padding: 15px; margin-bottom: 1rem; border-left: 4px solid {COLORS['crystal_blue']};">
            <h3 style="color: {COLORS['mystic_gold']}; margin: 0;">📐 向量模型 (Embedding)</h3>
        </div>
    """, unsafe_allow_html=True)
    st.caption("与对话模型使用同一 Ollama 服务（上方 URL），在此选择用于古籍向量化的模型。")
    emb_cfg = config_manager.get("embedding_engine") or {}
    if not isinstance(emb_cfg, dict):
        emb_cfg = {}
    current_emb_model = emb_cfg.get("model") or "nomic-embed-text"
    model_options = st.session_state.get("ollama_models", [])
    emb_index = 0
    if current_emb_model and current_emb_model in model_options:
        emb_index = model_options.index(current_emb_model)
    if model_options:
        selected_emb_model = st.selectbox(
            "选择向量模型（同服）",
            model_options,
            index=emb_index,
            help="与对话模型同一 Ollama 服务上的模型，如 nomic-embed-text、bge-m3 等",
        )
        if selected_emb_model != current_emb_model:
            config_manager.save_config("embedding_engine", {"model": selected_emb_model})
            kv = config_manager.get("knowledge_vault") or {}
            if not isinstance(kv, dict):
                kv = {}
            kv["embedding_model"] = selected_emb_model
            config_manager.save_config("knowledge_vault", kv)
            st.success(f"✅ 向量模型已设为 {selected_emb_model}")
    else:
        st.info("请先点击「测试连接 & 刷新模型列表」加载模型列表后，再选择向量模型。")
        manual_emb = st.text_input("或手动输入向量模型名", value=current_emb_model, key="manual_emb_model")
        if manual_emb and manual_emb != current_emb_model:
            config_manager.save_config("embedding_engine", {"model": manual_emb})
            st.success(f"✅ 向量模型已设为 {manual_emb}")

    st.divider()

    # ==================== 古籍入库 (Classical Canon Ingest) ====================
    st.markdown(f"""
        <div style="{GLASS_STYLE} padding: 15px; margin-bottom: 1rem; border-left: 4px solid {COLORS['teal_mist']};">
            <h3 style="color: {COLORS['mystic_gold']}; margin: 0;">📚 古籍入库 (Classical Canon)</h3>
        </div>
    """, unsafe_allow_html=True)
    st.caption("上传 TXT 古籍文件，将按段落切片并经当前向量模型入库，用于「古籍印证」检索。")
    uploaded = st.file_uploader("上传古籍 TXT (UTF-8)", type=["txt"], key="classical_txt_upload")
    book_col, chapter_col = st.columns(2)
    with book_col:
        ingest_book = st.text_input("书名（如《渊海子平》）", value="", key="ingest_source_book")
    with chapter_col:
        ingest_chapter = st.text_input("篇章（如《正官篇》）", value="", key="ingest_chapter")
    if uploaded and st.button("🚀 执行向量化入库"):
        try:
            from pathlib import Path
            import tempfile
            from data.vector_db.classical_db import ingest_file
            with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as tmp:
                tmp.write(uploaded.getvalue())
                tmp_path = Path(tmp.name)
            source = ingest_book or uploaded.name.replace(".txt", "")
            chapter = ingest_chapter or ""
            result = ingest_file(tmp_path, source_book=source, chapter=chapter, chunk_by="paragraph")
            tmp_path.unlink(missing_ok=True)
            st.success(f"✅ 入库完成：新增 {result['added']} 条，失败 {result['errors']} 条。")
        except Exception as e:
            st.error(f"入库失败: {e}")

