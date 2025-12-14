import streamlit as st
import os
import time

def render_self_learning():
    """Renders the Self-Learning main page."""
    st.header("🧠 自我进化矩阵 (Self-Learning Matrix)")
    with st.container():
        st.write("案例库连接: ✅ (Mock DB)")
        st.write("优化器状态: 待机")
        
        if 'sl_main_active' not in st.session_state: st.session_state['sl_main_active'] = None
        
        # Navigation Header
        if st.session_state['sl_main_active']:
             if st.button("⬅️ 返回矩阵首页 (Back to Matrix)", key="btn_back_matrix"):
                  st.session_state['sl_main_active'] = None
                  st.rerun()
             st.divider()
        
        if not st.session_state['sl_main_active']:
             _render_learning_grid()
        else:
             mode = st.session_state['sl_main_active']
             
             if "Optimizer" in mode:
                 _render_optimizer()
             elif "Video Learner" in mode or "Multimedia" in mode:
                 _render_multimedia_learning()
             # Removed Real Data Mining
             elif "Forum Mining" in mode:
                 _render_forum_mining()
             elif "Insights" in mode:
                 _render_insights_chat()
             elif "Theory Miner" in mode:
                 _render_theory_miner()
             elif "Task Manager" in mode:
                 _render_task_manager()
             # Web Learner is merged into Video Learner



def _render_learning_grid():
     st.markdown("### 🧩 核心进化引擎 (Evolution Engine)")
     
     # Row 1
     r1c1, r1c2, r1c3 = st.columns(3)
     with r1c1:
          with st.container(border=True):
              st.markdown("#### 🧬 古籍学习\n**(Theory Miner)**")
              st.caption("AI 阅读古籍提取规则")
              if st.button("进入学习", key="nav_theory", width="stretch"):
                   st.session_state['sl_main_active'] = "古籍学习 (Theory Miner)"
                   st.rerun()
     with r1c2:
          with st.container(border=True):
              st.markdown("#### 🎥 影音研习\n**(Multimedia)**")
              st.caption("视频听课 / 网络搜学")
              if st.button("进入学习", key="nav_vid", width="stretch"):
                   st.session_state['sl_main_active'] = "🎥 影音研习 (Multimedia)"
                   st.rerun()
     with r1c3:
          with st.container(border=True):
              st.markdown("#### 📋 任务中心\n**(Task Manager)**")
              st.caption("后台任务管理与监控")
              if st.button("查看任务", key="nav_tasks", width="stretch"):
                   st.session_state['sl_main_active'] = "📋 任务中心 (Task Manager)"
                   st.rerun()
     
     # Row 2
     r2c1, r2c2, r2c3 = st.columns(3)
     with r2c1:
          # Former Mining Console Slot - Now Empty or repurposed
          st.empty()
     with r2c2:
          with st.container(border=True):
              st.markdown("#### 💬 论坛潜水\n**(Forum Mining)**")
              st.caption("挖掘论坛实战案例")
              if st.button("进入论坛", key="nav_forum", width="stretch"):
                   st.session_state['sl_main_active'] = "💬 论坛潜水 (Forum Mining)"
                   st.rerun()
     with r2c3:
          with st.container(border=True):
              st.markdown("#### ⚖️ 权重优化\n**(Optimizer)**")
              st.caption("神经网络自动进化")
              if st.button("启动优化", key="nav_opt", width="stretch"):
                   st.session_state['sl_main_active'] = "权重优化 (Optimizer)"
                   st.rerun()
                   
     # Row 3 (Insights moved down or integrated)
     # Since we replaced the middle slot, let's put Insights below or keep it.
     # User requested Forum Mining, so prioritize visibility.
     
def _render_forum_mining():
    """
    New Module: Forum Data Ingestion & Source Management
    """
    st.subheader("💬 论坛潜水 (Forum Data Mining)")
    st.caption("从专业命理论坛挖掘带真实反馈的高质量案例。")

    from learning.db import LearningDB
    db = LearningDB()

    # --- 1. Source Management ---
    with st.expander("🌐 挖掘源管理 (Source Management)", expanded=True):
        st.info("配置可信的命理论坛或数据来源。")
        
        # Default sources if not in DB (Implementation detail: We might need a table for sources, or just config)
        # For MVP, we manage a list in Session State or Config.
        # Let's check config first.
        from core.config_manager import ConfigManager
        cm = ConfigManager()
        stored_sources = cm.get("forum_sources", ["元亨利贞 (China)", "龙隐网 (LongYin)"])
        
        # UI
        sel_src = st.multiselect("已启用源", stored_sources, default=stored_sources, key="forum_src_multi")
        
        c_add, c_btn = st.columns([3, 1])
        new_src = c_add.text_input("添加新源 (名称或 URL)", placeholder="例如: 某某周易论坛")
        if c_btn.button("➕ 添加"):
            if new_src and new_src not in stored_sources:
                stored_sources.append(new_src)
                cm.set("forum_sources", stored_sources)
                st.toast(f"已添加源: {new_src}")
                st.rerun()

    st.divider()

    # --- 2. Ingestion Interface ---
    st.write("#### 📥 案例投喂 (Case Ingestion)")
    
    # --- 2. Ingestion Interface ---
    st.write("#### 📥 案例投喂 (Case Ingestion)")
    
    tab_text, tab_file, tab_crawl = st.tabs(["📝 文本粘贴 (Paste)", "📂 文件上传 (Upload)", "🕷️ 自动抓取 (Auto-Crawl)"])
    
    with tab_text:
        st.caption("直接将帖子内容（包含楼主排盘和反馈）粘贴于此。系统会自动识别结构。")
        raw_text = st.text_area("帖子内容", height=200, placeholder="[求测] 乾造：甲子... 反馈：辛丑年升职...")
        
        col_src_sel, col_action = st.columns([1, 1])
        src_tag = col_src_sel.selectbox("数据来源标签", sel_src if sel_src else ["Unknown"])
        
        if col_action.button("⛏️ 立即挖掘 (Mine Now)", type="primary"):
            if not raw_text or len(raw_text.strip()) < 5:
                st.warning(f"内容太短 (当前有效字数: {len(raw_text.strip()) if raw_text else 0})。请粘贴完整的八字排盘和反馈内容。")
            else:
                with st.spinner("🚀 正在启动 V6.0 挖掘机... (NLP Processing)"):
                    from learning.forum_miner import ForumMiner
                    miner = ForumMiner()
                    
                    # Run Synchronously for text paste
                    success = miner.process_thread_text(raw_text, source_id=f"Paste_{src_tag}")
                    
                    if success:
                        st.balloons()
                        st.success("✅ 挖掘成功！案例已入库。V5 引擎将在下次训练时吸收此经验。")
                    else:
                        st.error("❌ 挖掘失败。可能原因：未检测到完整八字或有效反馈。")
                        st.info("提示：请确保内容中包含 '年/月/日/时' 或 '乾造/坤造' 以及 '反馈' 关键词。")

    with tab_file:
        st.caption("批量上传包含多个案例的 TXT 文件。")
        up_file = st.file_uploader("上传文件", type=['txt'])
        if up_file and st.button("📂 批量处理"):
            content = up_file.getvalue().decode("utf-8", errors="ignore")
            # Create a background job for bulk
            payload = {"type": "forum_bulk", "content_snippet": content[:100], "full_content_path": "TEMP_PATH"} # TODO: Save temp
            # For simplicity in this turn, run sync or save to temp
            st.info("构建中... 请使用文本粘贴模式。")

    with tab_crawl:
        st.error("⚠️ 警告：自动抓取属于高风险操作，请严格遵守礼貌协议。")
        st.info("此模式将模拟浏览器访问指定板块，自动翻页并提取带反馈的帖子。")
        
        c_url, c_pg = st.columns([3, 1])
        target_url = c_url.text_input("板块 URL (Board URL)", value="http://bbs.china95.net/forum-103-1.html", help="例如元亨利贞的八字实例反馈版")
        max_pages = c_pg.number_input("抓取页数", min_value=1, max_value=5, value=1)
        
        if st.button("🕷️ 启动爬虫任务 (Start Crawler Job)"):
            if "china95" not in target_url and "longyin" not in target_url:
                st.warning("目前仅支持 YuanHengLiZhen (china95) 或 LongYin 论坛的自动解析。")
            else:
                # Create Job
                payload = {
                    "type": "forum_crawl", 
                    "url": target_url, 
                    "max_pages": max_pages, 
                    "keywords": ["反馈", "准", "确实"] # Default keywords
                }
                # Assuming 'Forum Crawler' is a recognized internal job name or generic
                db.create_job("forum_crawl", target_file=f"Crawl {target_url[:20]}...", payload=payload)
                st.success(f"🚀 爬虫任务已创建！将在后台模拟人类行为进行抓取 (预计耗时: {max_pages * 2} 分钟)。")
                st.caption("请前往【任务中心】查看日志。")

def _render_optimizer():
    st.subheader("⚖️ 量子参数进化 (Quantum Evolution)")
    st.caption("基于贝叶斯逻辑 (Bayesian) 与 真实案例反馈 (Vreal Feedback) 的物理引擎自适应校正。")
    
    from learning.db import LearningDB
    from learning.optimizer import Optimizer
    
    db = LearningDB()
    opt = Optimizer()
    cases = db.get_all_cases()
    
    # 1. State Display
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.metric("📚 案例库规模", f"{len(cases)}", delta="样本数")
    with col_stat2:
        curr_gamma = opt.current_weights.get("gamma_decay", 1.5)
        st.metric("🌐 空间衰减系数 (γ)", f"{curr_gamma:.3f}", delta="物理常数")
    with col_stat3:
        # Mock Loss or Last Loss
        last_loss = 0.0 # TODO: Store in DB
        st.metric("📉 当前全局误差 (MSE)", f"{last_loss:.4f}", delta_color="inverse")

    st.divider()

    # 2. Manual Tweak vs Auto
    tab_auto, tab_manual = st.tabs(["🧬 自动进化 (Auto-Evolve)", "🎛️ 手动调参 (Manual Engineering)"])
    
    with tab_auto:
        st.markdown("#### 神经网络反向传播 (Gradient Descent)")
        st.write("系统将尝试通过微调物理参数（如 γ, $W_{Month}$）来减小预测值与真实值之间的误差。")
        
        if st.button("🧬 启动一轮迭代 (Run 1 Epoch)", type="primary"):
            if len(cases) < 5:
                st.warning(f"⚠️ 样本不足 (当前 {len(cases)}/5)。请先在【实战挖掘】或【排盘反馈】中积累更多真实案例。")
            else:
                progress_bar = st.progress(0, text="初始化优化器...")
                with st.spinner("正在重构向量空间 (Re-Vectorizing)..."):
                    time.sleep(0.5)
                    progress_bar.progress(30, text="计算基准误差 (Baseline Loss)...")
                    
                    res = opt.run_training_step()
                    
                    progress_bar.progress(100, text="优化完成！")
                    
                    if res['result'] == "improved":
                        st.balloons()
                        st.success(f"✅ 进化成功! 误差大幅下降: {res['old_mse']:.4f} -> {res['new_mse']:.4f}")
                        st.write(f"**参数更新**: Gamma {curr_gamma} -> {opt.current_weights['gamma_decay']}")
                    elif res['result'] == "reverted":
                        st.info(f"🔄 本次尝试未获突破 (MSE {res['new_mse']:.4f} >= {res['old_mse']:.4f})，已回滚参数。")
                    else:
                        st.write(res)
                        
    with tab_manual:
        st.write("#### 物理常数覆写 (Override)")
        new_gamma = st.slider("Gamma (距离衰减)", 0.1, 5.0, float(curr_gamma), 0.1)
        w_month = st.slider("Month Weight (月令权重)", 1.0, 10.0, float(opt.current_weights.get('month_branch_weight', 4.0)), 0.1)
        
        if st.button("💾 强制保存参数"):
            opt.current_weights['gamma_decay'] = new_gamma
            opt.current_weights['month_branch_weight'] = w_month
            db.save_weights(opt.current_weights, 0, note="Manual Override")
            st.success("参数已强制更新！新模型将在下次训练时生效。")


def _render_multimedia_learning(): # Renamed function
    st.caption("🎥 影音学习实验室：听懂命理教学视频，扫描网络资源。") # Updated caption
    
    tab_av, tab_net = st.tabs(["🎧 本地听课 (File)", "🌍 全网搜学 (Network)"]) # Removed tab_chat
    
    # --- Tab 1: Local File ---
    with tab_av:
        st.write("#### 📤 上传音视频文件 (Whisper Listening)")
        media_file = st.file_uploader("上传音频/视频 (mp3/mp4)", type=['mp3', 'wav', 'mp4', 'm4a', 'mov'])
        
        if media_file:
            if media_file.type.startswith('video'):
                st.video(media_file)
            else: 
                st.audio(media_file)
            
            if st.button("👂 开始听课 (Transcribe & Learn)"):
                with st.spinner("🎧 正在聆听并转换为文字... (Loading Whisper & Transcribing)"):
                    import tempfile
                    suffix = "." + media_file.name.split('.')[-1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(media_file.getvalue())
                        tmp_path = tmp.name
                    
                    from learning.media_miner import MediaMiner
                    mm = MediaMiner(model_size="base") 
                    text = mm.transcribe(tmp_path)
                    os.remove(tmp_path)

                    if text.startswith("[Error"):
                        st.error(f"转录失败: {text}")
                    else:
                        st.subheader("📝 听课笔记 (Transcript)")
                        st.text_area("原文", text, height=200)
                        
                        if len(text) > 50:
                            st.info("🧠 正在理解并提取命理规则...")
                            from learning.theory_miner import TheoryMiner
                            tm = TheoryMiner(host=st.session_state.get('ollama_host', "http://localhost:11434"))
                            rules = tm.extract_rules(text)
                            
                            if rules:
                                st.success(f"从视频中学会了 {len(rules)} 条新规则！")
                                st.json(rules)
                                
                                from learning.db import LearningDB
                                db = LearningDB()
                                for r in rules:
                                    db.add_rule(r, source_book=f"[Video] {media_file.name}")
                                st.success("已存入知识库！")
                            else:
                                st.warning("未能从内容中提取出有效规则。")

    # --- Tab 2: Network ---
    with tab_net:
        st.write("#### 🌍 网络视频流分析 (Web Streams)")
        v_type = st.radio("来源类型", ["单个视频 (Video)", "频道/播放列表 (Channel/Playlist)"], horizontal=True)
        v_url = st.text_input("视频/频道 URL (YouTube/Bilibili/TikTok/X)")
        
        if st.button("💾 订阅并扫描 (Subscribe & Scan)"):
            if not v_url:
                st.warning("请输入 URL")
            else:
                from learning.db import LearningDB
                db = LearningDB()
                
                if "Channel" in v_type:
                    with st.spinner("正在解析频道元数据..."):
                        from learning.video_downloader import VideoDownloader
                        dl = VideoDownloader()
                        res = dl.get_channel_info(v_url)
                        if isinstance(res, tuple):
                            vids, ch_title = res
                        else:
                            vids, ch_title = res, v_url
    
                    if not vids and isinstance(ch_title, str) and "Error" in ch_title:
                         st.error(f"解析失败: {ch_title}")
                    else:
                         real_name = ch_title if ch_title and "Unknown" not in ch_title else v_url
                         is_new = db.add_channel(real_name, v_url, "YouTube", "Added via UI")
                         
                         if is_new:
                              st.success(f"📺 频道 [{real_name}] 已订阅！")
                         else:
                              st.info(f"🔄 正在更新频道 [{real_name}]...")
                        
                         if vids:
                            from learning.video_miner import VideoMiner
                            vm = VideoMiner()
                            history = vm.get_history()
                            for v in vids:
                                v_id = vm.get_video_id(v['url'])
                                is_done = v_id in history
                                v['Status'] = "✅ 已学" if is_done else "🆕 新课"
                                v['Select'] = not is_done
                                v['Video_ID'] = v_id
                            
                            st.session_state[f"scan_res_{v_url}"] = vids
                         else:
                             st.error("未能找到视频，请检查 URL")
                else:
                    st.warning("单视频模式请直接加入队列 (Single Video mode not supported for subscription yet)")
    
        st.markdown("#### 📺 已订阅频道 (Subscribed Channels)")
        from learning.db import LearningDB
        db = LearningDB()
        channels = db.get_all_channels()
        if channels:
            for ch in channels:
                with st.container():
                    c1, c3, c4 = st.columns([5, 1.5, 0.5])
                    c1.markdown(f"📺 **[{ch['name']}]({ch['url']})**")
                    
                    scan_key = f"scan_res_{ch['url']}"
    
                    if c3.button("🔍 扫描", key=f"scan_btn_{ch['id']}"):
                         with st.spinner(f"正在扫描 {ch['name']}..."):
                            from learning.video_downloader import VideoDownloader
                            dl = VideoDownloader()
                            res = dl.get_channel_info(ch['url'])
                            if isinstance(res, tuple):
                                 vids, fresh_name = res
                                 if fresh_name and "http" not in fresh_name and "Unknown" not in fresh_name:
                                      db.add_channel(fresh_name, ch['url'])
                            else:
                                 vids = res
                            
                            if not vids: vids = []
                            
                            from learning.video_miner import VideoMiner
                            vm = VideoMiner()
                            history = vm.get_history()
                            
                            for v in vids:
                                v_id = vm.get_video_id(v['url'])
                                is_done = v_id in history
                                v['Status'] = "✅ 已学" if is_done else "🆕 新课"
                                v['Select'] = not is_done 
                                v['Video_ID'] = v_id 
                            
                            st.session_state[scan_key] = vids
                            st.rerun()
    
                    if scan_key in st.session_state:
                        vids = st.session_state[scan_key]
                        with st.expander(f"📋 {ch['name']} - 视频列表", expanded=True):
                            if not vids:
                                st.warning("未找到视频")
                            else:
                                import pandas as pd
                                
                                c_tool_1, c_tool_2, c_tool_3, c_tool_4 = st.columns([0.8, 0.8, 1.4, 2])
                                with c_tool_1:
                                    if st.button("全选", key=f"all_{ch['id']}"):
                                        for v in vids: v['Select'] = True
                                        st.rerun()
                                with c_tool_2:
                                    if st.button("全不选", key=f"none_{ch['id']}"):
                                        for v in vids: v['Select'] = False
                                        st.rerun()
                                
                                with c_tool_3:
                                    sort_opt = st.selectbox("排序", ["最近更新 (Default)", "标题", "🆕 新课优先", "💬 字幕优先"], key=f"sort_{ch['id']}", label_visibility="collapsed")
                                    
                                if sort_opt == "标题":
                                    vids.sort(key=lambda x: x['title'])
                                elif sort_opt == "🆕 新课优先":
                                    vids.sort(key=lambda x: 0 if "新课" in x['Status'] else 1)
                                elif sort_opt == "💬 字幕优先":
                                    vids.sort(key=lambda x: 0 if "💬" in x['title'] else 1)
                                
                                if "字幕" in sort_opt:
                                    st.caption("注: 💬 仅代表快速扫描能检测到的包含字幕的视频 (Beta)。")
    
                                df = pd.DataFrame(vids)
                                edited_df = st.data_editor(
                                    df,
                                    column_config={
                                        "Select": st.column_config.CheckboxColumn("选择", required=True),
                                        "Status": st.column_config.TextColumn("状态", width="small"),
                                        "title": st.column_config.TextColumn("标题", width="large"),
                                        "url": st.column_config.LinkColumn("链接"),
                                    },
                                    disabled=["Status", "title", "url"],
                                    hide_index=True,
                                    width="stretch",
                                    key=f"editor_{ch['id']}"
                                )
                                
                                if st.button("📥 将选中视频加入队列", key=f"q_sel_{ch['id']}"):
                                    sel_rows = edited_df[edited_df['Select'] == True]
                                    
                                    if sel_rows.empty:
                                        st.warning("未选择任何视频")
                                    else:
                                        count = 0
                                        for idx, row in sel_rows.iterrows():
                                            payload = {"type": "video", "url": row['url'], "title": row['title']}
                                            db.create_job("video_learn", target_file=row['title'], payload=payload)
                                            count += 1
                                        
                                        st.success(f"已加入 {count} 个任务！")
                                        db.update_channel_last_scanned(ch['url'])
                                        time.sleep(1)
                                        del st.session_state[scan_key] 
                                        st.rerun()
                                
                                if st.button("收起列表", key=f"hide_{ch['id']}"):
                                    del st.session_state[scan_key]
                                    st.rerun()
                    
                    if c4.button("🗑️", key=f"del_ch_{ch['id']}"):
                        db.delete_channel(ch['url'])
                        st.rerun()

def _render_insights_chat(): # New function for Insights & Chat
    st.write("#### 💡 知识库与研讨 (Knowledge & Discussion)")
    from learning.db import LearningDB
    db = LearningDB()
    
    # 1. Rules Display
    rules = db.get_all_rules()
    st.caption(f"当前系统已习得 {len(rules)} 条命理规则。")
    
    with st.expander("查看所有规则 (View Rules)", expanded=False):
            if rules:
                import pandas as pd
                df_rules = pd.DataFrame(rules)
                # Fix for PyArrow ArrowInvalid error: Convert dict/list cols to string
                # Identify object columns and convert them to string representation
                for col in df_rules.columns:
                    if df_rules[col].dtype == 'object':
                        df_rules[col] = df_rules[col].apply(lambda x: str(x) if isinstance(x, (dict, list)) else x)
                
                st.dataframe(df_rules)
            else:
                st.info("暂无规则。请先通过听课或阅读积累知识。")
    
    # 2. Chat Interface
    st.divider()
    st.write("#### 💬 与系统论道 (Chat with Bazi AI)")
    
    if "learn_chat_msgs" not in st.session_state: st.session_state["learn_chat_msgs"] = []
    
    for msg in st.session_state["learn_chat_msgs"]:
            st.chat_message(msg["role"]).write(msg["content"])
            
    if prompt := st.chat_input("探讨命理规则..."):
            st.session_state["learn_chat_msgs"].append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            
            import ollama
            host = st.session_state.get('ollama_host')
            model = st.session_state.get('selected_model_name', 'qwen2.5')
            
            # Context Construction
            rule_summary = "\n".join([f"- {r.get('rule_name', 'Rule')}: {str(r)[0:100]}..." for r in rules[-20:]]) # Limit context
            
            sys_prompt = f"""
            你是一个正在不断学习进化的八字命理系统。
            你已经学会了以下规则（最近20条）：
            {rule_summary}
            
            用户是你的导师或研讨伙伴。请根据你的知识库回答问题，或者讨论新的感悟。
            """
            
            stream = ollama.Client(host=host).chat(
                model=model, 
                messages=[{'role': 'system', 'content': sys_prompt}] + st.session_state["learn_chat_msgs"],
                stream=True
            )
            
            with st.chat_message("assistant"):
                resp = st.write_stream(stream)
            st.session_state["learn_chat_msgs"].append({"role": "assistant", "content": resp})

def _render_theory_miner():
    """
    Renders the Theory Miner (Library) Interface with Categories.
    """
    st.subheader("📚 藏经阁 (Ancient Library)")
    
    book_dir = "data/books"
    os.makedirs(book_dir, exist_ok=True)
    
    # Layout: Left (List) | Right (Reader)
    c_list, c_reader = st.columns([1, 2])
    
    with c_list:
        st.write("#### 📂 分类索引 (Index)")
        
        # 1. Category Filter
        cat_filter = st.radio(
            "选择分类", 
            ["📜 经典古籍 (Classics)", "🎥 影音实录 (Transcripts)"], 
            horizontal=True,
            label_visibility="collapsed"
        )
        
        # 2. Get Files & Filter
        all_files = sorted([f for f in os.listdir(book_dir) if f.endswith('.txt')])
        
        def is_media(f):
            return f.startswith("[Media]") or f.startswith("[Video]") or f.startswith("[Audio]")
            
        if "Classics" in cat_filter:
            display_files = [f for f in all_files if not is_media(f)]
        else:
            display_files = [f for f in all_files if is_media(f)]
            
        # 3. File List
        if not display_files:
            st.info("此分类下暂无藏书。")
            selected_book = None
        else:
            # Use a unique key based on category to reset selection when switching tabs
            selected_book = st.radio("书目列表", display_files, label_visibility="collapsed", key=f"list_{cat_filter}")
            st.session_state['selected_book'] = selected_book

        st.divider()
        
        # 4. Upload / Delete Tools
        with st.expander("🛠️ 管理工具 (Manage)", expanded=False):
            tab_up, tab_del = st.tabs(["📥 入库", "🗑️ 焚毁"])
            
            with tab_up:
                up_type = st.selectbox("书籍类型", ["经典古籍", "影音实录"], index=0 if "Classics" in cat_filter else 1)
                uploaded_file = st.file_uploader("上传文件 (.txt)", type="txt", label_visibility="collapsed")
                
                if uploaded_file and st.button("确认入库"):
                    fname = uploaded_file.name
                    # Auto-tagging
                    if up_type == "影音实录" and not is_media(fname):
                        fname = f"[Media] {fname}"
                    elif up_type == "经典古籍" and is_media(fname):
                        # Attempt to strip tag if user insists it's classic? Or just leave it.
                        pass
                        
                    path = os.path.join(book_dir, fname)
                    if not os.path.exists(path):
                        with open(path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        st.toast(f"✅ 已入库: {fname}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.warning("文件已存在")
            
            with tab_del:
                if selected_book:
                    st.write(f"选中: **{selected_book}**")
                    if st.button("确认焚毁", type="primary"):
                         try:
                             os.remove(os.path.join(book_dir, selected_book))
                             st.toast("🔥 已焚毁")
                             time.sleep(0.5)
                             st.rerun()
                         except Exception as e:
                             st.error(str(e))
                else:
                    st.caption("请先在上方选择一本书")

    with c_reader:
        sel = st.session_state.get('selected_book')
        # Verify it exists in current dir (safety)
        if sel and os.path.exists(os.path.join(book_dir, sel)):
            book_name = sel
            path = os.path.join(book_dir, book_name)
            
            st.write(f"#### 📖 {book_name}")
            
            try:
                with open(path, "r", encoding='utf-8') as f:
                    content = f.read()
            except:
                try:
                     with open(path, "r", encoding='gb18030') as f:
                        content = f.read()
                except:
                    content = "⚠️ 无法解码文件内容。"
            
            # Context info
            col_info, col_act = st.columns([1, 1])
            with col_info:
                 st.caption(f"字数: {len(content)}")
                 tags = "🏷️ 古文/原著" if not is_media(book_name) else "🏷️ 语音转录/笔记"
                 st.caption(tags)
            
            with col_act:
                 if st.button("🧠 AI 深度研读 (Deep Mine)", width="stretch"):
                     from learning.db import LearningDB
                     db = LearningDB()
                     payload = {"type": "text_mining", "filename": book_name}
                     db.create_job("theory_mine", target_file=path, payload=payload)
                     st.info(f"🤖 书童已领命，正在后台研读《{book_name}》...")
            
            st.divider()
            st.text_area("Reader", content, height=600, label_visibility="collapsed")
            
        else:
            if not display_files:
                st.info("👈 请上传书籍")
            else:
                st.info("👈 请选择书籍开始阅读")

def _render_task_manager():
    st.subheader("📋 任务控制中心 (Job Control Center)")
    from learning.db import LearningDB
    from datetime import datetime
    from core.config_manager import ConfigManager
    import sqlite3
    import json
    import pandas as pd
    
    db = LearningDB()
    cm = ConfigManager()
    
    # --- 1. Top Stats & Config ---
    # 显示当前并发配置
    col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
    with col_cfg1:
        max_concurrent = cm.get('max_concurrent_jobs', 3)
        st.info(f"⚡ **最大并发数**: {max_concurrent} 个任务")
    with col_cfg2:
        subtitle_priority = cm.get('subtitle_priority', True)
        priority_text = "✅ 已开启" if subtitle_priority else "❌ 已关闭"
        st.info(f"💬 **字幕优先级**: {priority_text}")
    with col_cfg3:
        # Deduplicate Button here for visibility
        if st.button("🧹 合并重复任务", width="stretch", help="自动保留进度最快的一个，清理重复项"):
            count = db.deduplicate_jobs()
            if count > 0:
                st.success(f"✅ 已清理 {count} 个重复任务！")
                time.sleep(1)
                st.rerun()
            else:
                st.info("没有发现重复任务。")
    
    st.divider()
    
    # --- 2. Filter & Controls ---
    col_ctrl1, col_ctrl2 = st.columns([4, 1])
    with col_ctrl1:
        # Multi-select status filter
        status_options = ['running', 'pending', 'paused', 'failed', 'finished']
        status_labels =  ['🟢 运行中', '🔵 等待中', '🟡 已暂停', '🔴 失败', '✅ 已完成']
        
        # Smart default: Show all relevant including finished for better feedback
        default_statuses = ['running', 'pending', 'paused', 'failed', 'finished']
        
        selected_statuses = st.multiselect(
            "筛选任务状态",
            status_options,
            default=default_statuses,
            format_func=lambda x: dict(zip(status_options, status_labels)).get(x, x)
        )
    with col_ctrl2:
         st.write("") # Spacer
         if st.button("🔄 刷新列表", width='stretch'):
             st.rerun()
         
         if st.checkbox("自动刷新 (Auto)", value=False, key="task_auto_refresh"):
             time.sleep(3)
             st.rerun()

    # Get Jobs
    jobs = db.get_jobs_by_status(selected_statuses if selected_statuses else status_options, limit=1000)
    
    if not jobs:
        st.info("✨ 没有符合条件的任务。")
        return

    # --- 3. Data Processing for View ---
    # Convert to DataFrame for Data Editor
    
    # Helper for elapsed time
    def calc_elapsed_time(created_at_str):
        try:
            created = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
            elapsed = datetime.now() - created
            hours = int(elapsed.total_seconds() // 3600)
            minutes = int((elapsed.total_seconds() % 3600) // 60)
            if hours > 0: return f"{hours}h {minutes}m"
            if minutes > 0: return f"{minutes}m"
            return "<1m"
        except: return "N/A"

    data_list = []
    for j in jobs:
        try: payload = json.loads(j['payload']) if j['payload'] else {}
        except: payload = {}
        
        title = payload.get('title', os.path.basename(j['target_file']))
        url = payload.get('url', '')
        
        # Type Map
        t_map = {'video_learn': '🎥 视频', 'theory_mine': '📚 古籍', 'case_mine': '⛏️ 挖掘'}
        
        # Progress map
        pct = 0
        if j['total_work'] > 0:
            pct = int((j['current_progress'] / j['total_work']) * 100)
        
        data_list.append({
            "Select": False,
            "ID": j['id'],
            "Status": j['status'],
            "Type": t_map.get(j['job_type'], j['job_type']),
            "Title": title,
            "Progress": pct,
            "Created": j['created_at'][5:16], # mm-dd HH:MM
            "Elapsed": calc_elapsed_time(j['created_at']),
            "_full_job": j # Hidden store
        })
        
    df = pd.DataFrame(data_list)
    
    # --- 4. Main Table View (Data Editor) ---
    st.write(f"共 **{len(jobs)}** 个任务")
    
    edited_df = st.data_editor(
        df,
        column_config={
            "Select": st.column_config.CheckboxColumn("选择", width="small"),
            "ID": st.column_config.NumberColumn("ID", width="small"),
            "Status": st.column_config.TextColumn("状态", width="small"),
            "Type": st.column_config.TextColumn("类型", width="small"),
            "Title": st.column_config.TextColumn("任务标题", width="large"),
            "Progress": st.column_config.ProgressColumn("进度", min_value=0, max_value=100, format="%d%%"),
            "Created": st.column_config.TextColumn("创建时间", width="medium"),
            "Elapsed": st.column_config.TextColumn("耗时", width="small"),
            "_full_job": None # Hide
        },
        disabled=["ID", "Status", "Type", "Title", "Progress", "Created", "Elapsed"],
        hide_index=True,
        width="stretch",
        key="job_editor"
    )
    
    # Get Selected IDs
    selected_rows = edited_df[edited_df['Select'] == True]
    selected_ids = selected_rows['ID'].tolist()
    
    # --- 5. Bulk Actions Footer ---
    if selected_ids:
        st.markdown(f"### 🛠️ 对选中的 {len(selected_ids)} 个任务执行操作:")
        
        b1, b2, b3, b4 = st.columns(4)
        
        with b1:
            if st.button("▶️ 批量恢复/开始", width="stretch"):
                db.batch_update_status(selected_ids, 'pending')
                st.success(f"已恢复 {len(selected_ids)} 个任务")
                time.sleep(1)
                st.rerun()
                
        with b2:
            if st.button("⏸️ 批量暂停", width="stretch"):
                db.batch_update_status(selected_ids, 'paused')
                st.success(f"已暂停 {len(selected_ids)} 个任务")
                time.sleep(1)
                st.rerun()
                
        with b3:
            if st.button("🔄 批量重试 (归零)", width="stretch"):
                # Retry implies pending + reset progress
                db.batch_update_status(selected_ids, 'pending')
                for jid in selected_ids:
                    db.update_job_progress(jid, 0, 3) # Reset to 0
                st.success(f"已重置 {len(selected_ids)} 个任务")
                time.sleep(1)
                st.rerun()
                
        with b4:
            if st.button("🗑️ 批量删除", type="primary", width="stretch"):
                db.batch_delete_jobs(selected_ids)
                st.success(f"已删除 {len(selected_ids)} 个任务")
                time.sleep(1)
                st.rerun()
    else:
        # Show global cleanup if nothing selected
        st.caption("提示: 在上方表格勾选任务后可进行批量操作。")
        with st.expander("更多全局操作"):
            g1, g2 = st.columns(2)
            with g1:
                if st.button("🗑️ 清理所有已完成任务"):
                    count = db.delete_completed_jobs()
                    st.success(f"清理了 {count} 个历史任务")
                    time.sleep(1)
                    st.rerun()
            with g2:
                if st.button("⚠️ 暂停全部任务 (Panic Button)"):
                    active = db.get_jobs_by_status(['running', 'pending'])
                    ids = [j['id'] for j in active]
                    if ids:
                         db.batch_update_status(ids, 'paused')
                         st.success(f"已强制暂停 {len(ids)} 个活跃任务")
                         time.sleep(1)
                         st.rerun()

