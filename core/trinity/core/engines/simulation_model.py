
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

class SimulationModel:
    """
    📦 SimulationModel (ASE)
    
    Manages the state of the Antigravity Synthetic Evolution (ASE) system.
    Stores session configs, running progress, and aggregated results.
    """
    
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root
        self.reports_dir = os.path.join(workspace_root, "reports")
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Session State
        self.is_running = False
        self.processed_count = 0
        self.total_target = 10000
        self.start_time: Optional[datetime] = None
        
        # Statistics State
        self.summary_stats: Dict[str, Any] = {}
        self.singularities: List[Dict[str, Any]] = []
        
        # Configuration
        self.config = {
            "batch_size": 10000,
            "geo_variance": 0.2,
            "damping_factor": 1.0
        }

    def reset_progress(self, target: int):
        self.processed_count = 0
        self.total_target = target
        self.start_time = datetime.now()
        self.singularities = []
        self.summary_stats = {}

    def save_baseline(self, data: Dict[str, Any]):
        filename = f"ase_baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path = os.path.join(self.reports_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path

    def load_latest_baseline(self) -> Optional[Dict[str, Any]]:
        files = [f for f in os.listdir(self.reports_dir) if f.startswith("ase_baseline_")]
        if not files:
            # Check for standard baseline
            std_path = os.path.join(self.reports_dir, "ase_phase_1_baseline.json")
            if os.path.exists(std_path):
                with open(std_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return None
            
        files.sort(reverse=True)
        with open(os.path.join(self.reports_dir, files[0]), "r", encoding="utf-8") as f:
            return json.load(f)
