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
    
    # ==================== LLM 配置 ====================
    st.markdown(f"""
        <div style="{GLASS_STYLE} padding: 15px; margin-bottom: 1rem; border-left: 4px solid {COLORS['rose_magenta']};">
            <h3 style="color: {COLORS['mystic_gold']}; margin: 0;">🤖 大模型神启（LLM 核心）</h3>
        </div>
    """, unsafe_allow_html=True)
    st.caption("所选对话模型将用于「全息格局」页的 LLM 判词与格局解读；系统会要求模型以**简体中文**输出。若为 Qwen 3.5 等思考模型，判词将自动以「关闭思考流」方式调用，直接输出正文。")
    col_llm_1, col_llm_2 = st.columns([1, 1])
    
    with col_llm_1:
        ollama_host = st.text_input(
            "Ollama 服务地址",
            value=st.session_state.get("ollama_host", "http://localhost:11434"),
            help="本地或远程 Ollama 服务 URL，如 http://localhost:11434",
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

    with st.expander("🛠️ 连接与模型", expanded=True):
        if st.button("📡 测试连接并刷新模型列表"):
            try:
                client = ollama.Client(host=ollama_host)
                resp = client.list()
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
                st.success(f"✅ 连接成功，发现 {len(models)} 个模型")
                config_manager.save_config("ollama_host", ollama_host)
            except Exception as e:
                st.error(f"❌ 连接失败: {e}")

        model_options = st.session_state.get('ollama_models', [])
        index = 0
        current_selection = st.session_state.get("selected_model_name", "")
        if current_selection and current_selection in model_options:
            index = model_options.index(current_selection)
        saved_model = config_manager.get("selected_model_name")

        if model_options:
            selected_model_name = st.selectbox(
                "选择对话模型（用于判词与解读）",
                model_options,
                index=index,
                help="该模型将在全息格局页生成 LLM 判词（简体中文）。Qwen 3.5 等思考模型会以 think=False 调用，判词直接输出正文。",
            )
            if selected_model_name != st.session_state.get("selected_model_name"):
                st.session_state["selected_model_name"] = selected_model_name
                config_manager.save_config("selected_model_name", selected_model_name)
                ai_cfg = config_manager.get("ai_engine") or {}
                if not isinstance(ai_cfg, dict):
                    ai_cfg = {}
                ai_cfg["chat_model"] = selected_model_name
                config_manager.save_config("ai_engine", ai_cfg)

            if st.button("🟢 验证模型响应（测试）"):
                try:
                    with st.spinner("正在发送测试请求（简体中文）…"):
                        client = ollama.Client(host=ollama_host)
                        kwargs = {
                            "model": selected_model_name,
                            "messages": [{"role": "user", "content": "请用一句简体中文回复：已就绪。"}],
                            "stream": False,
                        }
                        try:
                            res = client.chat(**{**kwargs, "think": False})
                        except TypeError:
                            res = client.chat(**kwargs)
                        # 兼容 chat 返回 message.content 与 generate 返回 response
                        text = ""
                        if hasattr(res, "message") and res.message is not None:
                            text = getattr(res.message, "content", None) or ""
                        if not text and hasattr(res, "response"):
                            text = res.response or ""
                        if not text and isinstance(res, dict):
                            msg = res.get("message") or {}
                            text = msg.get("content", "") if isinstance(msg, dict) else ""
                        if not text:
                            text = "（无文本）"
                        text = (text or "").strip() or "（无文本）"
                        st.success(f"✅ 模型响应正常：{text[:200]}{'…' if len(text) > 200 else ''}")
                except Exception as e:
                    st.error(f"❌ 模型无响应或超时：{e}")
        else:
            if saved_model:
                st.info(f"上次使用的模型：{saved_model}（请先测试连接以刷新列表）")
            else:
                st.info("请先点击「测试连接并刷新模型列表」以加载模型列表。")

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

    st.divider()

    # ==================== 030: 矩阵微调实验区 (TMM Lab) ====================
    st.markdown(f"""
        <div style="{GLASS_STYLE} padding: 15px; margin-bottom: 1rem; border-left: 4px solid {COLORS['mystic_gold']};">
            <h3 style="color: {COLORS['mystic_gold']}; margin: 0;">🔬 矩阵微调实验区 (TMM Lab)</h3>
        </div>
    """, unsafe_allow_html=True)
    st.caption("十神→5D 映射矩阵（TMM）为 FDS 的「重力常数」。可切换推理用矩阵版本并微调权重；全量大模型审计与 V5 生成请运行 scripts/matrix_logic_auditor.py 或 matrix_backfitting_auditor.py。")
    try:
        from pathlib import Path
        import json as _json
        _root = Path(__file__).resolve().parent.parent.parent
        _v4 = _root / "config" / "physics" / "tensor_mapping_matrix_V4.0_BETA.json"
        _v5 = _root / "config" / "physics" / "tensor_mapping_matrix_V5.0_ALPHA.json"
        _manifest = _root / "config" / "patterns" / "manifest_A01.json"
        _physics = config_manager.get("physics") or {}
        if not isinstance(_physics, dict):
            _physics = {}
        _saved_ver = _physics.get("matrix_version", "4.0-BETA")
        _opts = ["4.0-BETA"]
        if _v5.exists():
            _opts.append("5.0-ALPHA")
        _choice = st.radio("推理用矩阵", options=_opts, index=_opts.index(_saved_ver) if _saved_ver in _opts else 0, key="tmm_version_switch", horizontal=True)
        if _choice != _saved_ver:
            _physics["matrix_version"] = _choice
            config_manager.save_config("physics", _physics)
            st.success(f"已切换为 **{_choice}**，排盘与流形归位将使用该矩阵。")
        _tmm = None
        _ver = "3.0"
        _source_label = ""
        _source_path = ""
        if _choice == "5.0-ALPHA" and _v5.exists():
            with open(_v5, "r", encoding="utf-8") as _f:
                _d = _json.load(_f)
                _tmm = _d.get("tensor_mapping_matrix", _d)
                _ver = _d.get("version", "5.0-ALPHA")
                _source_label = "物理核心 (V5 校准)"
                _source_path = "config/physics/tensor_mapping_matrix_V5.0_ALPHA.json"
        if not _tmm and _v4.exists():
            with open(_v4, "r", encoding="utf-8") as _f:
                _d = _json.load(_f)
                _tmm = _d.get("tensor_mapping_matrix", _d)
                _ver = _d.get("version", "4.0-BETA")
                _source_label = "物理核心 (全链路生效)"
                _source_path = "config/physics/tensor_mapping_matrix_V4.0_BETA.json"
        if not _tmm and _manifest.exists():
            with open(_manifest, "r", encoding="utf-8") as _f:
                _tmm = _json.load(_f).get("tensor_mapping_matrix")
                _ver = "3.0"
                _source_label = "法律基准 (manifest 出厂)"
                _source_path = "config/patterns/manifest_A01.json"
        if _tmm and _tmm.get("weights"):
            _gods = _tmm.get("ten_gods", list(_tmm["weights"].keys()))
            _dims = _tmm.get("dimensions", ["E", "O", "M", "S", "R"])
            _labels = {"E": "能量E", "O": "秩序O", "M": "财富M", "S": "压力S", "R": "关系R"}
            _god_cn = {"ZG": "正官", "PG": "七杀", "ZR": "正财", "PR": "偏财", "ZS": "食神", "PS": "伤官", "ZC": "正印", "PC": "枭神", "ZB": "比肩", "PB": "劫财"}
            if st.session_state.get("tmm_edited_version") != _ver:
                st.session_state["tmm_edited"] = {g: list(_tmm["weights"][g]) for g in _gods}
                st.session_state["tmm_edited_version"] = _ver
            edited = st.session_state["tmm_edited"]
            st.info(f"**当前加载**：{_source_label} · 版本 **{_ver}** · `{_source_path}`")
            st.caption("切换版本后，排盘与全息归位将使用所选矩阵；V4/V5 敏感度对比可运行：`scripts/matrix_logic_auditor.py --generate-v5 --compare`。")
            st.caption("十神×5维 权重表（可编辑后保存草稿）")
            for _g in _gods:
                _row = list(edited.get(_g, [0] * 5)[:5])
                _cols = st.columns(6)
                with _cols[0]:
                    _display = f"{_god_cn.get(_g, _g)} ({_g})"
                    st.text_input("十神", value=_display, key=f"tmm_lab_{_g}", disabled=True, label_visibility="collapsed")
                for _i, _dim in enumerate(_dims[:5]):
                    with _cols[_i + 1]:
                        _v = st.number_input(
                            _labels.get(_dim, _dim),
                            value=round(_row[_i], 2),
                            format="%.2f",
                            key=f"tmm_{_g}_{_dim}",
                            label_visibility="visible",
                        )
                        _row[_i] = float(_v)
                edited[_g] = _row
            st.session_state["tmm_edited"] = edited
            _sample_vec = [1.0] * 10
            _p = [0.0] * 5
            for _i, _g in enumerate(_gods):
                _w = edited.get(_g, [0] * 5)
                for _j in range(5):
                    _p[_j] += _sample_vec[_i] * (_w[_j] if _j < len(_w) else 0)
            with st.expander("📐 预览：标准向量 [1,1,…,1] 的 5D 投影", expanded=False):
                st.write("E: {:.3f}, O: {:.3f}, M: {:.3f}, S: {:.3f}, R: {:.3f}".format(*_p))
            _chat_model = (config_manager.get("ai_engine") or {}).get("chat_model", "qwen2.5:32b")
            if st.button("🧠 请大模型给矩阵第一印象", key="btn_tmm_first_impression"):
                try:
                    _summary = _json.dumps(edited, ensure_ascii=False, indent=2)
                    _prompt = (
                        "作为命理物理学家，请对下面这份「十神→五维(E/O/M/S/R)」映射权重矩阵给出你的「第一印象」："
                        "是否符合古典命理中十神与秩序/能量/财富/压力/关系的对应？用 2～4 句话概括。\n\n" + _summary
                    )
                    with st.spinner(f"大模型 ({_chat_model}) 正在阅读矩阵…"):
                        _host = config_manager.get("ollama_host") or "http://localhost:11434"
                        _client = ollama.Client(host=_host)
                        _r = _client.chat(model=_chat_model, messages=[{"role": "user", "content": _prompt}], options={"num_predict": 300})
                    if isinstance(_r, dict):
                        _content = (_r.get("message") or {}).get("content") or ""
                    else:
                        _content = getattr(getattr(_r, "message", None), "content", None) or ""
                    _content = (_content or "").strip()
                    if _content:
                        st.session_state["tmm_first_impression"] = _content
                    else:
                        st.error("模型返回为空。请确认 Ollama 已加载该模型且未超时；可到终端执行同模型对话测试。")
                except Exception as _e:
                    st.error(f"请求失败: {_e}")
            if st.session_state.get("tmm_first_impression"):
                with st.expander("📜 大模型对当前矩阵的第一印象", expanded=True):
                    st.write(st.session_state["tmm_first_impression"])
            if st.button("💾 保存为草稿 (tmm_draft.json)", key="btn_tmm_save_draft"):
                _out = _root / "results" / "tmm_draft.json"
                _out.parent.mkdir(parents=True, exist_ok=True)
                with open(_out, "w", encoding="utf-8") as _f:
                    _json.dump({"version": "draft", "ten_gods": _gods, "dimensions": _dims, "weights": edited}, _f, ensure_ascii=False, indent=2)
                st.success(f"已保存至 {_out}。可用于 matrix_logic_auditor 或对比脚本。")
        else:
            st.caption("未找到 TMM 配置（manifest_A01.json 或 config/physics/tensor_mapping_matrix_V4.0_BETA.json）。")
    except Exception as e:
        st.caption(f"矩阵加载失败: {e}")

