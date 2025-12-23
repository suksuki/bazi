import sys
import os
import json

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.profile_manager import ProfileManager
from core.trinity.core.oracle import TrinityOracle
from core.trinity.core.nexus.definitions import BaziParticleNexus

def list_and_scan_profiles():
    pm = ProfileManager()
    profiles = pm.get_all()
    oracle = TrinityOracle()
    
    print(f"📋 Found {len(profiles)} profiles in archive.\n")
    
    for p in profiles:
        name = p.get('name')
        gender = p.get('gender')
        date_str = f"{p.get('year')}-{p.get('month'):02d}-{p.get('day'):02d} {p.get('hour'):02d}h"
        
        # Calculate Bazi for scanning
        # Using a simple conversion here for the demo
        from core.calculator import BaziCalculator
        calc = BaziCalculator(p['year'], p['month'], p['day'], p['hour'], p.get('minute', 0))
        chart = calc.get_chart()
        bazi = [
            f"{chart['year']['stem']}{chart['year']['branch']}",
            f"{chart['month']['stem']}{chart['month']['branch']}",
            f"{chart['day']['stem']}{chart['day']['branch']}",
            f"{chart['hour']['stem']}{chart['hour']['branch']}"
        ]
        dm = bazi[2][0]
        
        # Scan with Oracle
        res = oracle.analyze(bazi, dm)
        interactions = res.get('interactions', [])
        
        print(f"👤 Profile: {name} ({gender}) | {date_str}")
        print(f"   Bazi: {' '.join(bazi)} | DM: {dm}")
        
        if interactions:
            print("   🔗 Active Triggers:")
            for inter in interactions:
                print(f"     - [{inter['id']}] {inter['type']}: {inter['name']} (Priority: {inter['priority']})")
        else:
            print("   ⚪ No specific triggers detected.")
        
        resonance = res.get('resonance')
        print(f"   📉 State: {resonance.mode} | Sync: {resonance.sync_state:.2f} | Follow: {resonance.is_follow}")
        print("-" * 50)

if __name__ == "__main__":
    list_and_scan_profiles()
