import sys
import os
import time
import json
import traceback
import logging

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from learning.db import LearningDB

# Config Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [Miner] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("MinerService")

class MinerService:
    def __init__(self):
        self.db = LearningDB()
        self.active = True
        self.poll_interval = 5 # seconds
        logger.info("Miner Service Initialized (Dual-Core Architecture [Yin System]).")

    def run(self):
        logger.info("Entering Main Loop...")
        while self.active:
            try:
                processed = self.process_next_job()
                if not processed:
                    time.sleep(self.poll_interval)
            except KeyboardInterrupt:
                logger.info("Stopping Service...")
                self.active = False
            except Exception as e:
                logger.error(f"Critical Loop Error: {e}")
                traceback.print_exc()
                time.sleep(5)

    def process_next_job(self):
        # Fetch pending jobs (FIFO)
        pending = self.db.get_jobs_by_status(['pending'], limit=1)
        
        if not pending:
            return False

        job = pending[0]
        job_id = job['id']
        job_type = job['job_type']
        
        logger.info(f"Picked up Job #{job_id}: {job_type}")
        self.db.update_job_status(job_id, 'running')
        
        try:
            if job_type in ['video_mining', 'video_learn']:
                self.handle_video_mining(job)
            elif job_type in ['model_training', 'train_model']:
                self.handle_model_training(job)
            elif job_type == 'theory_mine':
                 self.handle_file_mining(job)
            elif job_type == 'case_mine':
                 self.handle_case_mining(job)
            elif job_type == 'auto_mine':
                 self.handle_auto_mine(job)
            else:
                logger.warning(f"Unknown job type: {job_type}. Marking failed.")
                self.db.update_job_status(job_id, 'failed')
                return

            self.db.update_job_status(job_id, 'finished')
            self.db.update_job_progress(job_id, 100, 100)
            logger.info(f"Job #{job_id} Finished Successfully.")
            
        except Exception as e:
            logger.error(f"Job #{job_id} Failed: {e}")
            self.db.update_job_status(job_id, 'failed')
            # In a real system, we might save the error message to the DB
            
        return True

    def handle_video_mining(self, job):
        """
        Orchestrates VideoMiner (Download) -> TheoryMiner (Extract).
        payload: { "url": "...", "max_videos": 5 }
        """
        from learning.video_miner import VideoMiner
        from learning.theory_miner import TheoryMiner
        
        payload = json.loads(job['payload'])
        url = payload.get('url')
        max_videos = int(payload.get('max_videos', 5))
        
        if not url:
            raise ValueError("No URL provided.")
            
        vm = VideoMiner()
        tm = TheoryMiner() # LLM Client
        
        # 1. Resolve Targets
        video_ids = []
        if "list=" in url or "/channel/" in url or "/@ " in url:
            logger.info(f"Fetching channel/playlist: {url}")
            vids, err = vm.get_channel_videos(url)
            if err:
                raise Exception(f"Channel fetch failed: {err}")
            video_ids = vids[:max_videos]
        else:
            vid = vm.get_video_id(url)
            if vid:
                video_ids = [vid]
            else:
                raise Exception("Invalid YouTube URL")
        
        total_vids = len(video_ids)
        logger.info(f"Found {total_vids} videos to process.")
        self.db.update_job_progress(job['id'], 0, total_vids)
        
        # 2. Process Loop
        success_count = 0
        
        for idx, vid in enumerate(video_ids):
            try:
                v_url = f"https://www.youtube.com/watch?v={vid}"
                
                # Check history?
                # Using vm.get_history() is not efficient inside loop if list is huge, 
                # but let's assume naive check for now or rely on user intent.
                # Actually, let's skip check to force run if user requested.
                
                logger.info(f"[{idx+1}/{total_vids}] Processing: {v_url}")
                
                # A. Get Transcript
                text, err = vm.fetch_transcript(v_url)
                
                if err == "WHISPER_FALLBACK":
                    logger.info("  -> Downloading Audio for Whisper...")
                    audio_path, dl_err = vm.download_audio(v_url)
                    if not audio_path:
                        logger.warning(f"  -> Audio download failed: {dl_err}")
                        continue
                        
                    logger.info("  -> Transcribing with Whisper...")
                    text, t_err = vm.transcribe_file(audio_path)
                    if t_err:
                         logger.warning(f"  -> Transcription failed: {t_err}")
                         continue
                elif err != "Success":
                    logger.warning(f"  -> Transcript failed: {err}")
                    continue
                
                if not text or len(text) < 50:
                    logger.warning("  -> Text too short, skipping.")
                    continue
                    
                # B. Pre-Cleaning (New V25.0)
                from learning.text_cleaner import TextCleaner
                raw_len = len(text)
                cleaned_text = TextCleaner.clean(text)
                clean_len = len(cleaned_text)
                logger.info(f"  -> Pre-Cleaning: {raw_len} -> {clean_len} chars (Removed Garbage)")
                
                if clean_len < 50:
                     logger.warning("  -> Text empty after cleaning, skipping.")
                     continue

                # C. Mine Knowledge
                logger.info(f"  -> Mining Knowledge...")
                
                # Split huge text?
                if clean_len > 5000:
                    # chunk it
                    chunks = [cleaned_text[i:i+4000] for i in range(0, clean_len, 4000)]
                    for chunk in chunks:
                        rules = tm.extract_rules(chunk)
                        if rules and "error" not in rules:
                             tm.save_rule(rules)
                else:
                    rules = tm.extract_rules(cleaned_text)
                    if rules and "error" not in rules:
                         tm.save_rule(rules)
                
                success_count += 1
                vm.mark_processed(vid)
                
            except Exception as e:
                logger.error(f"Error processing video {vid}: {e}")
            
            # Update Progress
            self.db.update_job_progress(job['id'], idx + 1, total_vids)
            
        vm.cleanup_temp_files()
        logger.info(f"Video Mining Complete. Success: {success_count}/{total_vids}")

    def handle_model_training(self, job):
        from core.trainer import ModelTrainer
        payload = json.loads(job['payload'])
        aspect = payload.get('aspect', 'wealth')
        
        logger.info(f"Starting Model Training for: {aspect}")
        trainer = ModelTrainer()
        result = trainer.train(aspect=aspect)
        
        if not result:
            raise Exception("Training returned False")
        logger.info("Training Completed.")

    def handle_file_mining(self, job):
        """
        Process a text file for theory rules.
        """
        from learning.theory_miner import TheoryMiner
        job_id = job['id']
        target_file = job['target_file']
        
        logger.info(f"Mining Theory from file: {target_file}")
        
        if not os.path.exists(target_file):
            # Check relative to project root?
            if os.path.exists(os.path.join("data/books", os.path.basename(target_file))):
                target_file = os.path.join("data/books", os.path.basename(target_file))
            else:
                 raise FileNotFoundError(f"File not found: {target_file}")
            
        with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        tm = TheoryMiner()
        # Use generator to update progress
        processed_chunks = 0
        
        # Generator returns chunks
        gen = tm.process_book(content, chunk_size=2000)
        
        for result in gen:
            processed_chunks += 1
            rules = result['rules']
            for r in rules:
                 r['source_book'] = os.path.basename(target_file)
                 tm.save_rule(r)
            
            prog = int((result['chunk_index'] / result['total_chunks']) * 100)
            self.db.update_job_progress(job_id, prog, 100)
                 
        logger.info(f"Finished mining {target_file}")

    def handle_case_mining(self, job):
        """
        Process a text file and extract Case Studies.
        """
        target_file = job['target_file']
        job_id = job['id']
        payload = json.loads(job['payload'])
        use_new_db = payload.get('target_db') == 'cases.db'
        
        logger.info(f"Mining Cases from file: {target_file} (NewDB={use_new_db})")
        
        if not os.path.exists(target_file):
             if os.path.exists(os.path.join("data/books", os.path.basename(target_file))):
                target_file = os.path.join("data/books", os.path.basename(target_file))
             else:
                raise FileNotFoundError(f"File not found: {target_file}")
            
        with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        if use_new_db:
            # --- V2 Pipeline (Crimson Vein) ---
            from service.processor import ContentProcessor
            from service.sanitizer import Sanitizer
            
            # Chunking
            chunks = [content[i:i+5000] for i in range(0, len(content), 5000)]
            processor = ContentProcessor()
            
            for idx, chunk in enumerate(chunks):
                clean_chunk = Sanitizer.clean_text(chunk)
                try:
                    processor.process_text(clean_chunk, source_url=f"File: {os.path.basename(target_file)}")
                except Exception as e:
                    logger.error(f"Chunk processing error: {e}")
                
                prog = int(((idx+1)/len(chunks)) * 100)
                self.db.update_job_progress(job_id, prog, 100)
                
        else:
            # --- Legacy Logic ---
            from learning.theory_miner import TheoryMiner
            tm = TheoryMiner()
            chunks = [content[i:i+8000] for i in range(0, len(content), 8000)]
            for idx, chunk in enumerate(chunks):
                cases = tm.mine_cases_from_text(chunk)
                if cases:
                    logger.info(f"Found {len(cases)} cases in chunk {idx}")
                    for c in cases:
                        self.db.add_case(
                            c.get('name', 'Unknown'), 
                            c.get('chart'), 
                            c.get('truth'), 
                            source=os.path.basename(target_file)
                        )
                
                prog = int(((idx+1)/len(chunks)) * 100)
                self.db.update_job_progress(job_id, prog, 100)
            
            prog = int(((idx+1)/len(chunks)) * 100)
            self.db.update_job_progress(job_id, prog, 100)

    def handle_auto_mine(self, job):
        """
        Executes the AutoMiner autonomous loop.
        """
        payload = json.loads(job['payload'])
        cycles = int(payload.get('cycles', 3))
        job_id = job['id']
        
        logger.info(f"🤖 Auto-Miner Initiated. Cycles: {cycles}")
        
        from service.auto_miner import AutoMiner
        miner = AutoMiner()
        # This is blocking, but that's fine for this service model
        miner.start_autopilot(max_cycles=cycles)
        logger.info(f"✅ Auto-Miner Mission Complete.")

if __name__ == "__main__":
    service = MinerService()
    try:
        service.run()
    except KeyboardInterrupt:
        pass
