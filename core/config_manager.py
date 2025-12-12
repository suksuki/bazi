
import json
import os

class ConfigManager:
    # 默认配置
    DEFAULT_CONFIG = {
        'max_concurrent_jobs': 3,  # 提高默认并发数到3
        'subtitle_priority': True,  # 优先使用字幕
        'subtitle_languages': ['zh-Hans', 'zh-Hant', 'zh-CN', 'zh-TW', 'zh', 'en'],  # 字幕语言优先级
        'ollama_host': 'http://localhost:11434',
        'selected_model_name': 'qwen2.5'
    }
    
    def __init__(self, config_file="data/config.json"):
        self.config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), config_file)
        self._ensure_dir()

    def _ensure_dir(self):
        dirname = os.path.dirname(self.config_file)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    def load_config(self):
        if not os.path.exists(self.config_file):
            return {}
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def save_config(self, key, value):
        config = self.load_config()
        config[key] = value
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
            
    def get(self, key, default=None):
        config = self.load_config()
        # 优先使用配置文件中的值，其次使用默认配置，最后使用传入的default
        return config.get(key, self.DEFAULT_CONFIG.get(key, default))
