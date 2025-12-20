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

    def save_profile(self, profile_id=None, name=None, gender=None, year=None, month=None, day=None, hour=None, minute=0, city=None, longitude=None):
        """
        Save or update a profile.
        
        If profile_id is provided and exists, update that profile.
        Otherwise, create a new profile.
        
        This is the preferred method for saving profiles as it uses ID-based identification.
        """
        profiles = self._load_data()
        
        # Normalize name: strip whitespace
        name = name.strip() if name else name
        
        # Find existing profile by ID
        existing_idx = None
        if profile_id:
            existing_idx = next((i for i, p in enumerate(profiles) if p.get('id') == profile_id), None)
        
        new_profile = {
            "id": profile_id if existing_idx is not None else str(uuid.uuid4()),
            "name": name,
            "gender": gender,  # "男" or "女"
            "year": int(year),
            "month": int(month),
            "day": int(day),
            "hour": int(hour),
            "minute": int(minute) if minute else 0,
            "city": city if city and city != "None" else None,
            "longitude": float(longitude) if longitude else None,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if existing_idx is not None:
            # Update existing profile (keep original created_at if possible)
            original_created_at = profiles[existing_idx].get('created_at')
            if original_created_at:
                new_profile['created_at'] = original_created_at
            new_profile['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            profiles[existing_idx] = new_profile
        else:
            # Insert new profile
            profiles.insert(0, new_profile)  # Newest first
        
        self._save_data(profiles)
        return True, new_profile['id']

    def add_profile(self, name, gender, year, month, day, hour, minute=0, city=None, longitude=None):
        """
        Legacy method for adding profiles. Uses name-based duplicate detection.
        Consider using save_profile() for new code.
        """
        profiles = self._load_data()
        
        # Normalize name: strip whitespace
        name = name.strip() if name else name
        
        # Check duplicate (Simple check by Name, also strip existing names for matching)
        existing_idx = next((i for i, p in enumerate(profiles) if p.get('name', '').strip() == name), None)

        new_profile = {
            "id": str(uuid.uuid4()) if existing_idx is None else profiles[existing_idx]['id'],
            "name": name,
            "gender": gender, # "男" or "女"
            "year": int(year),
            "month": int(month),
            "day": int(day),
            "hour": int(hour),
            "minute": int(minute) if minute else 0,
            "city": city if city and city != "None" else None,
            "longitude": float(longitude) if longitude else None,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if existing_idx is not None:
            # Update existing profile
            profiles[existing_idx] = new_profile
        else:
            # Insert new profile
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
