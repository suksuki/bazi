import signal
import sys
import time
import logging
from core.scheduler import BackgroundWorker

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [Worker] %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("data/logs/worker_process.log", encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    logger.info("Received termination signal. Shutting down worker...")
    worker.stop()
    sys.exit(0)

if __name__ == "__main__":
    logger.info("🚀 Starting Independent Background Worker Process...")
    
    # Register Signal Handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    worker = BackgroundWorker(check_interval=5) # Slower interval for stability
    
    # Start worker thread (it's threaded internally)
    worker.start()
    
    logger.info("✅ Worker active. Waiting for tasks...")
    
    # Keep main process alive
    try:
        while True:
            time.sleep(1)
            if not worker.is_alive():
                logger.error("Worker thread died unexpectedly!")
                break
    except KeyboardInterrupt:
        logger.info("Worker stopped by user.")
        worker.stop()
