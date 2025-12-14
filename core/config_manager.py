import json
import os
from typing import Dict, Any
from threading import Lock

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "tuning_params.json")

# 默认参数 (如果文件不存在)
DEFAULT_CONFIG = {
    "physics": {
        "stem_score": 10,
        "branch_main_qi": 10,
        "branch_sub_qi": 7,
        "gan_zhi_overlap_ratio": 0.5
    },
    "seasonal": {
        "monthly_command_bonus": 1.5,  # 得令加成
        "generation_bonus": 1.2        # 印绶加成
    },
    "phase": {
        "scorched_earth_threshold": 0.8 # 焦土阈值
    },
    "calibration": {
        "mae_threshold": 4.0
    }
}

class ConfigManager:
    """
    配置管理器 (Single Source of Truth)
    负责读取和写入 config/tuning_params.json
    支持热重载 (Hot-Reload)
    """
    _lock = Lock()
    _cached_config = None
    _last_mtime = 0

    @staticmethod
    def _ensure_dir():
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)

    @staticmethod
    def load_config() -> Dict[str, Any]:
        """读取配置 (引擎和UI都调这个)"""
        ConfigManager._ensure_dir()
        
        if not os.path.exists(CONFIG_PATH):
            #如果不存，写入默认配置
            ConfigManager.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG
        
        try:
            # 简单的文件修改时间检查，用于缓存失效 (可选，但为了实时性先每次读取)
            # 在高并发下可能需要缓存优化，但对于 Streamlit + 单人调试，直接读写即可
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Config load failed: {e}, using default.")
            return DEFAULT_CONFIG

    @staticmethod
    def save_config(new_config: Dict[str, Any]):
        """保存配置 (AI和侧边栏都调这个)"""
        ConfigManager._ensure_dir()
        
        with ConfigManager._lock: # 线程安全锁，防止同时写入冲突
            # 读取旧配置，进行合并更新 (防止覆盖掉未传的参数)
            try:
                if os.path.exists(CONFIG_PATH):
                    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                        current = json.load(f)
                else:
                    current = DEFAULT_CONFIG.copy()
            except:
                current = DEFAULT_CONFIG.copy()
            
            # Deep update (recurisvie update for nested dicts)
            ConfigManager._deep_update(current, new_config)
            
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(current, f, indent=4, ensure_ascii=False)
            
            # print("💾 参数已热更新并保存！")

    @staticmethod
    def _deep_update(base_dict, update_dict):
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                ConfigManager._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    @staticmethod
    def get_param(section: str, key: str, default=None):
        """Helper to get a specific value"""
        cfg = ConfigManager.load_config()
        return cfg.get(section, {}).get(key, default)

    def get(self, key: str, default=None):
        """Instance method to mimic dict.get on the root config"""
        cfg = ConfigManager.load_config()
        return cfg.get(key, default)
