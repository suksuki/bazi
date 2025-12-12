import json
import os
import uuid
from datetime import datetime

class ProfileManager:
    def __init__(self, data_file="data/profiles.json"):
        # Resolve absolute path relative to this file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.file_path = os.path.join(base_dir, data_file)
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def _load_data(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def _save_data(self, data):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_profile(self, name, gender, year, month, day, hour):
        profiles = self._load_data()
        
        # Check duplicate (Simple check by Name)
        if any(p['name'] == name for p in profiles):
            # Update existing or throw error? Let's auto-update/overwrite for now or create distinct
            # For simplicity, allow duplicates but use UUID
            pass

        new_profile = {
            "id": str(uuid.uuid4()),
            "name": name,
            "gender": gender, # "男" or "女"
            "year": int(year),
            "month": int(month),
            "day": int(day),
            "hour": int(hour),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        profiles.insert(0, new_profile) # Newest first
        self._save_data(profiles)
        return True, "Profile saved successfully."

    def delete_profile(self, profile_id):
        profiles = self._load_data()
        new_profiles = [p for p in profiles if p['id'] != profile_id]
        if len(new_profiles) == len(profiles):
            return False, "Profile not found."
        self._save_data(new_profiles)
        return True, "Profile deleted."

    def get_all(self):
        return self._load_data()

    def search(self, query):
        profiles = self._load_data()
        if not query:
            return profiles
        return [p for p in profiles if query.lower() in p['name'].lower()]
