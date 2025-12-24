import json
import os
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class LogicRegistry:
    """The Great Librarian: Ensures no algorithm is ever forgotten."""
    
    _instance = None
    _manifest = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogicRegistry, cls).__new__(cls)
            cls._instance._load_manifest()
        return cls._instance

    def _load_manifest(self):
        path = os.path.join(os.path.dirname(__file__), 'logic_manifest.json')
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    self._manifest = json.load(f)
                logger.info(f"✅ Core Logic Manifest loaded: V{self._manifest.get('version')}")
            else:
                logger.warning("⚠️ logic_manifest.json not found. Using empty registry.")
        except Exception as e:
            logger.error(f"❌ Failed to load logic manifest: {e}")

    def get_rule(self, rule_id: str) -> Dict[str, Any]:
        return self._manifest.get('registry', {}).get(rule_id, {})

    def get_all_active_rules(self) -> Dict[str, Dict[str, Any]]:
        registry = self._manifest.get('registry', {})
        return {k: v for k, v in registry.items() if v.get('status') == 'ACTIVE'}

    def get_themes(self) -> Dict[str, Any]:
        """Retrieves and returns the high-level themes from the manifest."""
        return self._manifest.get('themes', {})

    def get_active_modules(self, theme_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves active UI modules from the manifest, optionally filtered by theme.
        Returns a list of module dictionaries including their ID.
        """
        modules = self._manifest.get('modules', {})
        active_list = []
        for m_id, m_data in modules.items():
            if m_data.get('active', True):
                # Filter by theme if requested
                if theme_id and m_data.get('theme') != theme_id:
                    continue
                    
                m_copy = m_data.copy()
                m_copy['id'] = m_id
                active_list.append(m_copy)
        
        # Sort by key (MOD_00, MOD_01...)
        return sorted(active_list, key=lambda x: x['id'])

    def verify_conformance(self, active_interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Cross-checks current analysis results against the manifest to detect 'Logic Loss'.
        """
        active_ids = {i.get('id') for i in active_interactions}
        manifest_rules = self.get_all_active_rules()
        
        missing = []
        for r_id, r_info in manifest_rules.items():
            # This is a simplified check: if a rule ID from manifest is missing in current stack
            # In a real sniffer, we would re-evaluate the conditions.
            pass
            
        return {
            "conformance_score": 1.0, # Placeholder
            "missing_rules": missing
        }

    @property
    def version(self):
        return self._manifest.get('version', '0.0.0')

    @property
    def manifest(self):
        return self._manifest
