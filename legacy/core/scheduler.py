import time
import threading
import json
import traceback
from learning.db import LearningDB
from learning.theory_miner import TheoryMiner

class BackgroundWorker(threading.Thread):
    def __init__(self, check_interval=2):
        super().__init__(daemon=True)
        self.db = LearningDB()
        self.check_interval = check_interval
        self._stop_event = threading.Event()
        
        # 读取配置并初始化Miner
        from core.config_manager import ConfigManager
        cm = ConfigManager()
        ollama_host = cm.get('ollama_host', 'http://localhost:11434')
        self.miner = TheoryMiner(host=ollama_host)
        
        self.active_futures = {} # {job_id: future}

    def run(self):
        """
        Main loop: Polls DB for jobs and manages ThreadPool.
        """
        import concurrent.futures
        from core.config_manager import ConfigManager
        
        # Create a pool with sufficient max threads. We utilize config to limit logical concurrency.
        # Hard limit 10 to prevent system exhaustion.
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        
        print("Background Worker Started (Optimized Concurrent)")
        
        while not self._stop_event.is_set():
            try:
                # 0. Clean finished futures
                done_ids = [jid for jid, f in self.active_futures.items() if f.done()]
                for jid in done_ids: 
                    # Check for exceptions
                    try:
                        self.active_futures[jid].result() # Re-raise exception if any
                    except Exception as e:
                        print(f"Job {jid} crashed: {e}")
                        # Optionally mark as failed in DB if not handled
                        # process_job usually handles it, but bare exceptions might escape
                    
                    del self.active_futures[jid]

                # 1. Load Config
                try:
                    cm = ConfigManager()
                    limit = int(cm.get('max_concurrent_jobs', 1))
                except: 
                    limit = 1
                
                # 2. Get Jobs
                jobs = self.db.get_jobs_by_status(['pending', 'running'])
                running_db = [j for j in jobs if j['status'] == 'running']
                pending_db = [j for j in jobs if j['status'] == 'pending']
                
                # 3. Resume interrupted 'running' jobs (Restart logic)
                # If DB says running but we aren't tracking it, it must be from previous session
                for job in running_db:
                    if job['id'] not in self.active_futures:
                        print(f"Resuming interrupted job {job['id']}...")
                        f = executor.submit(self.process_job, job)
                        self.active_futures[job['id']] = f
                
                # 4. Schedule New Jobs
                current_load = len(self.active_futures)
                slots = limit - current_load
                
                if slots > 0 and pending_db:
                    # Strategy: FIFO (Oldest First). 
                    # DB returns DESC (Newest First). Reverse it.
                    oldest_first = pending_db[::-1]
                    
                    for i in range(min(slots, len(oldest_first))):
                        job = oldest_first[i]
                        print(f"Starting new job {job['id']}...")
                        # Mark Running FIRST to prevent double scheduling if loop is tight
                        self.db.update_job_status(job['id'], 'running')
                        
                        f = executor.submit(self.process_job, job)
                        self.active_futures[job['id']] = f
                        
                time.sleep(self.check_interval)
                
            except Exception as e:
                print(f"Worker Loop Error: {e}")
                traceback.print_exc()
                time.sleep(5)

    def stop(self):
        self._stop_event.set()

    def process_job(self, job):
        """
        处理单个任务，具有完整的异常处理和恢复能力
        """
        job_id = job['id']
        
        try:
            payload = json.loads(job['payload'])
            job_type = payload.get('type', 'book')
            
            # Mark as running if pending
            if job['status'] == 'pending':
                self.db.update_job_status(job_id, 'running')
                
            print(f"[{job_id}] ▶️  开始处理任务 [{job_type}]: {job['target_file']}")
            
            # 根据任务类型分发
            if job_type == 'video':
                self._process_video_job(job, payload)
            elif job_type == 'case_mine':
                self._process_case_mining_job(job, payload)
            elif job_type == 'forum_crawl':
                self._process_forum_crawl_job(job, payload) 
            elif job_type == 'auto_mine':
                self._process_auto_mine_job(job, payload)
            else:
                self._process_book_job(job, payload)
                
            print(f"[{job_id}] ✅ 任务完成")
            
        except json.JSONDecodeError as e:
            # Payload 解析错误
            error_msg = f"Payload格式错误: {e}"
            print(f"[{job_id}] ❌ {error_msg}")
            self.db.update_job_status(job_id, 'failed')
            self._log_error(job_id, error_msg)
            
        except KeyboardInterrupt:
            # 用户中断，优雅退出
            print(f"[{job_id}] ⚠️  收到中断信号，保存进度...")
            self.db.update_job_status(job_id, 'paused')
            raise
            
        except Exception as e:
            # 任何其他异常都不应该导致整个worker崩溃
            error_msg = f"未预期错误: {type(e).__name__}: {str(e)}"
            print(f"[{job_id}] ❌ {error_msg}")
            traceback.print_exc()
            
            # 标记为失败，但不影响其他任务
            self.db.update_job_status(job_id, 'failed')
            self._log_error(job_id, error_msg)

    def _process_forum_crawl_job(self, job, payload):
        """
        Executes a forum crawling task (V6.1 Protocol).
        """
        job_id = job['id']
        start_url = payload.get('url')
        max_pages = int(payload.get('max_pages', 1))
        
        from learning.crawler_utils import SafeCrawler
        from learning.miners.china95 import China95Parser
        import re
        
        crawler = SafeCrawler()
        parser = China95Parser()
        
        # 1. Page Loop
        current_page_url = start_url
        processed_threads = 0
        valid_cases = 0
        
        for page_num in range(1, max_pages + 1):
            if self.db.get_job(job_id)['status'] == 'paused': return
            
            print(f"[{job_id}] Crawling Board Page {page_num}: {current_page_url}")
            board_html = crawler.polite_get(current_page_url)
            
            if not board_html:
                print(f"[{job_id}] Failed to fetch board page.")
                break
                
            # 2. Extract Thread Links (China95 Specific Regex)
            # Pattern: <a href="thread-12345-1-1.html" ... >
            # Note: We need absolute URLs.
            # Base domain assumption: 
            domain = "http://bbs.china95.net/"
            if "longyin" in start_url: domain = "http://www.longyin.net/" 
            
            # Simple Regex for href
            # thread-(\d+)-1-1.html
            thread_ids = set(re.findall(r'thread-(\d+)-1-1\.html', board_html))
            print(f"[{job_id}] Found {len(thread_ids)} threads on page.")
            
            total_threads_on_page = len(thread_ids)
            for idx, tid in enumerate(thread_ids):
                if self.db.get_job(job_id)['status'] == 'paused': return
                
                t_url = f"{domain}thread-{tid}-1-1.html"
                
                # Fetch Thread
                t_html_text = crawler.polite_get(t_url)
                if not t_html_text: continue
                
                # 3. Parse Thread (Data Mining)
                # Parse HTML to List of Posts?
                # For simplified v6.1, we simulate a 'list of posts' structure 
                # OR we update Parser to handle raw HTML.
                # Currently parser expects: [{'user':..., 'content':...}]
                # We need a mini-adapter here to parse raw HTML -> Post List.
                
                # Simple split by "发表于" or author div class to verify structure?
                # Let's try to just feed raw text if parser supports fallback, 
                # but parser specific logic relies on 'user' field for OP check.
                
                # Regex to find OP Content (Rough)
                # China95 structure: <div class="t_fsz"> ... </div>
                # This is hard without BeautifulSoup.
                # Let's try to identify OP by just assuming first big text block is OP
                # and looking for "楼主:" or relying on the Parser's logic.
                
                # Update: We will mock the 'posts' structure for the parser using simple regex splitting
                # expecting standard Discuz! format.
                
                # Just for safety, we extract the whole text and try to pass it as single string
                # If Parser sees string, it treats as OP only.
                # But we need feedback. Feedback is in replies.
                
                # Attempt to split by '发表于' which separates posts in text dump usually
                raw_posts = t_html_text.split("发表于")
                posts_struct = []
                for i, p_text in enumerate(raw_posts):
                   if i == 0: continue # Header junk
                   # Extract user? <a href="space-uid-..." class="xw1">UserName</a>
                   u_match = re.search(r'class="xw1">([^<]+)</a>', p_text)
                   user = u_match.group(1) if u_match else f"User_{i}"
                   
                   # Content? class="t_fsz"
                   # Strip tags
                   clean_content = re.sub(r'<[^>]+>', '', p_text)
                   posts_struct.append({'user': user, 'content': clean_content})
                
                if not posts_struct:
                     # Fallback to pure text
                     posts_struct = [{'user': 'OP', 'content': re.sub(r'<[^>]+>', '', t_html_text)}]

                # Run Miner
                result = parser.parse_thread(posts_struct)
                
                if result and result.get('data_quality_score', 0) > 0.6:
                    # Valid Case!
                    print(f"[{job_id}] ✅ Mined Valid Case: {t_url}")
                    
                    bazi = result['bazi_input']
                    truth = result['ground_truth_events']
                    
                    # Construct Case Name
                    case_name = f"Forum_{tid}_{bazi.get('year_val','Unknown')}"
                    
                    # Save to DB
                    self.db.add_case(
                        name=case_name,
                        chart_data=bazi, # Note: this is raw input, DB validates normalization
                        ground_truth=truth,
                        source="China95_Crawler"
                    )
                    valid_cases += 1
                
                processed_threads += 1
                # Progress Update (Page granularity or Thread granularity?)
                # current_progress is int. Let's send processed count
                self.db.update_job_progress(job_id, processed_threads, total_threads_on_page * max_pages)

            # Next Page logic...
            # Usually URL scheme allows simple increment: forum-103-2.html
            # Update current_page_url
            next_pg = page_num + 1
            # Regex replace last number? forum-103-1.html -> forum-103-2.html
            current_page_url = re.sub(r'-(\d+)\.html', f'-{next_pg}.html', current_page_url)

        self.db.update_job_status(job_id, 'finished')
        print(f"[{job_id}] Crawling Finished. Mined {valid_cases} cases.")
            

    def _log_error(self, job_id, error_msg):
        """记录错误到日志文件"""
        import os
        from datetime import datetime
        
        log_dir = "data/logs"
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, "task_errors.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] Job {job_id}: {error_msg}\n")

    def _process_video_job(self, job, payload):
        job_id = job['id']
        url = payload.get('url')
        
        # Step 1: Download (if not done)
        # Check progress. 0 = Start, 1 = Audio Downloaded, 2 = Transcribed, 3 = mined
        progress = job['current_progress']
        
        from learning.video_downloader import VideoDownloader
        from learning.media_miner import MediaMiner
        from core.config_manager import ConfigManager
        import os
        
        downloader = VideoDownloader()
        cm = ConfigManager()
        
        # --- Stage 1: Download ---
        if progress < 1:
            print(f"[{job_id}] Downloading/Subs...")
            
            # 检查是否启用字幕优先级
            fetch_subs = cm.get('subtitle_priority', True)
            
            # Unpack 4 values
            file_path, title, duration, is_subtitle = downloader.download_audio(url, fetch_subs=fetch_subs)
            if not file_path:
                self.db.update_job_status(job_id, 'failed')
                return
            
            payload['local_path'] = file_path # If subtitle, this is txt path
            payload['title'] = title
            payload['is_sub'] = is_subtitle
            
            # If subtitle, skip transcription stage
            if is_subtitle:
               self.db.update_job_progress(job_id, 2, 3) # Skip to 2
            else:
               self.db.update_job_progress(job_id, 1, 3) # Go to 1
        else:
            # Resume logic: Redownload if needed
            fetch_subs = cm.get('subtitle_priority', True)
            file_path, title, duration, is_subtitle = downloader.download_audio(url, fetch_subs=fetch_subs)
            
        # Check pause
        if self.db.get_job(job_id)['status'] == 'paused': return

        # --- Stage 2: Transcribe (Only if Audio) ---
        t_filename = f"[Video] {title}.txt".replace("/","_")
        
        # Determine progress state again
        # If is_subtitle is True, we essentially have the transcript.
        if is_subtitle:
            # Copy subtitle txt to book dir
            book_dir = "data/books"
            os.makedirs(book_dir, exist_ok=True)
            t_path = os.path.join(book_dir, t_filename)
            
            # Read sub content
            with open(file_path, 'r', errors='ignore') as f: sub_text = f.read()
            # Write to book
            with open(t_path, "w") as f: f.write(sub_text)
            
            # Cleanup temp sub
            downloader.cleanup(file_path)
            
        elif progress < 2:
            print(f"[{job_id}] Transcribing Audio...")
            mm = MediaMiner(model_size="base") 
            text = mm.transcribe(file_path)
            
            # Cleanup Audio
            downloader.cleanup(file_path)
            
            if not text or text.startswith("[Error"):
                self.db.update_job_status(job_id, 'failed')
                return
            
            book_dir = "data/books"
            os.makedirs(book_dir, exist_ok=True)
            t_path = os.path.join(book_dir, t_filename)
            with open(t_path, "w") as f:
                f.write(text)
                
            self.db.update_job_progress(job_id, 2, 3)
        
        # Check pause
        if self.db.get_job(job_id)['status'] == 'paused': return

        # --- Stage 3: Smart Mining (Knowledge Cortex) ---
        if progress <= 2: # No longer just mining, but "Knowledge Processing"
            print(f"[{job_id}] Intelligent Analysis (Cortex Active)...")
            from learning.knowledge_processor import KnowledgeProcessor
            
            # 读取ollama配置
            ollama_host = cm.get('ollama_host', 'http://localhost:11434')
            kp = KnowledgeProcessor(ollama_host=ollama_host)
            
            t_path = os.path.join("data/books", t_filename)
            with open(t_path, 'r') as f: content = f.read()
            
            # Chunking (Manual or helper?)
            chunk_size = 3000
            chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
            
            for i, chunk in enumerate(chunks):
                 # Cortex processing
                 # It saves data internally
                 try:
                    res = kp.process_content_chunk(chunk, source_meta=url)
                    ext_count = len(res.get('extracted', []))
                    if ext_count > 0:
                        print(f"  Chunk {i+1}: Found {ext_count} items [{res['type']}]")
                 except Exception as e:
                    print(f"  Chunk {i+1} Error: {e}")
                 
            self.db.update_job_progress(job_id, 3, 3)
            self.db.update_job_status(job_id, 'finished')
            self.db.mark_book_read(t_filename)
            
            # Update Video Miner History
            try:
                from learning.video_miner import VideoMiner
                vm = VideoMiner()
                # Extract ID from URL
                vid_id = vm.get_video_id(url)
                if vid_id:
                    vm.mark_processed(vid_id)
            except Exception as e:
                print(f"Failed to mark history: {e}")
                
            print(f"[{job_id}] Video Processed & Cleaned.")


    def _process_book_job(self, job, payload):
        job_id = job['id']
        target_file = job['target_file']
        current_progress = job['current_progress']
        model = payload.get('model', 'qwen2.5')
        
        # Load content
        import os
        file_path = os.path.join("data/books", target_file)
        if not os.path.exists(file_path):
            self.db.update_job_status(job_id, 'failed')
            return

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Start Processing
        chunk_iterator = self.miner.process_book(content, model=model, chunk_size=3000)
        
        # Skip previously done chunks
        for chunk_res in chunk_iterator:
            chunk_idx = chunk_res['chunk_index']
            total_chunks = chunk_res['total_chunks']
            
            if chunk_idx <= current_progress:
                continue
                
            # Check for Pause signal
            current_job_state = self.db.get_job(job_id)
            if current_job_state['status'] == 'paused':
                print(f"Job {job_id} paused by user.")
                return 
            
            self.db.update_job_progress(job_id, chunk_idx, total_chunks)
            if chunk_res.get('rule'):
                rule_data = chunk_res['rule']
                rule_data['source_book'] = target_file
                self.db.add_rule(rule_data, source_book=target_file)
        
        self.db.update_job_status(job_id, 'finished')
        self.db.mark_book_read(target_file)
        print(f"Job {job_id} Finished.")

    def _process_case_mining_job(self, job, payload):
        job_id = job['id']
        target_file = job['target_file']
        model = payload.get('model') 
        use_new_db = payload.get('target_db') == 'cases.db'
        
        import os
        import time
        file_path = os.path.join("data/books", target_file)
        if not os.path.exists(file_path):
             self.db.update_job_status(job_id, 'failed')
             return

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
             content = f.read()

        # Chunking: 5000 chars per chunk for Processor focus
        chunk_size = 5000
        total_len = len(content)
        chunks = [content[i:i+chunk_size] for i in range(0, total_len, chunk_size)]
        
        total_items_found = 0
        
        # New Pipeline: Use Processor
        if use_new_db:
            from service.processor import ContentProcessor
            from service.sanitizer import Sanitizer
            processor = ContentProcessor()
            
            for i, chunk in enumerate(chunks):
                # Check pause
                if self.db.get_job(job_id)['status'] == 'paused': return
                self.db.update_job_progress(job_id, i+1, len(chunks))
                
                # Sanitize & Process
                clean_chunk = Sanitizer.clean_text(chunk)
                
                # Processor handles classification and DB insertion internally
                # We mainly rely on it to find "CASE" content.
                # Since chunk might be mixed, we might want to use a specific extraction mode if we know it's cases.
                # But allowing Processor to classify is safer.
                try:
                    processor.process_text(clean_chunk, source_url=f"File: {target_file} (Chunk {i})")
                    total_items_found += 1 # Rough count, as process_text doesn't return count per se
                except Exception as e:
                    print(f"[{job_id}] Processor Error on chunk {i}: {e}")

        else:
            # --- OLD LOGIC (Legacy Support) ---
            chunk_size = 15000 # Larger chunk for old miner
            chunks = [content[i:i+chunk_size] for i in range(0, total_len, chunk_size)]

            for i, chunk in enumerate(chunks):
                 if self.db.get_job(job_id)['status'] == 'paused': return
                 self.db.update_job_progress(job_id, i+1, len(chunks))
                 
                 # Mine Cases
                 cases = self.miner.mine_cases_from_text(chunk, model=model)
                 if cases:
                     for c in cases:
                          if 'chart' in c and isinstance(c['chart'], dict) and 'year' in c['chart']:
                                if 'name' not in c: c['name'] = f"Case_{int(time.time())}_{total_items_found}"
                                self.db.add_case(c['name'], c['chart'], c.get('truth', {}), source=target_file)
                                total_items_found += 1

                 # Mine Rules
                 try:
                     rule_result = self.miner.extract_rules(chunk, model=model)
                     rules_list = rule_result if isinstance(rule_result, list) else [rule_result] if isinstance(rule_result, dict) else []
                     for r in rules_list:
                         r['source_book'] = target_file
                         self.db.add_rule(r, source_book=target_file)
                 except Exception as e:
                     print(f"[{job_id}] Theory Mining Warning: {e}")
        
        print(f"[{job_id}] Deep Mining (NewDB={use_new_db}) Finished. Items processed: {total_items_found}")
        self.db.update_job_status(job_id, 'finished')

    def _process_auto_mine_job(self, job, payload):
        """
        Executes the AutoMiner autonomous loop.
        """
        job_id = job['id']
        cycles = int(payload.get('cycles', 3))
        mode = payload.get('mode', 'mixed')
        
        print(f"[{job_id}] 🤖 Auto-Miner Initiated. Mode: {mode}, Cycles: {cycles}")
        
        # Lazy import to avoid circular dependencies if any
        from service.auto_miner import AutoMiner
        
        try:
            miner = AutoMiner()
            # We run the miner. Note: start_autopilot prints to stdout.
            # Ideally we'd capture output or have miner update DB progress.
            # But for now, we just let it run.
            
            miner.start_autopilot(max_cycles=cycles, mode=mode)
            
            self.db.update_job_status(job_id, 'finished')
            print(f"[{job_id}] ✅ Auto-Miner Mission Complete.")
            
        except Exception as e:
            error_msg = f"Auto-Miner Crash: {e}"
            print(f"[{job_id}] ❌ {error_msg}")
            self.db.update_job_status(job_id, 'failed')
            self._log_error(job_id, error_msg)

