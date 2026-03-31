from lunar_python import Solar, Lunar
import math
from datetime import timedelta, datetime

class BaziCalculator:
    def __init__(self, year, month, day, hour, minute=0, longitude=None, tz_offset=8):
        """
        year, month, day, hour, minute: Local Standard Time
        longitude: Observer's longitude (degrees). Default None (skips correction).
        tz_offset: Timezone offset in hours (default +8 for CNS).
        """
        self.solar_raw = Solar.fromYmdHms(year, month, day, hour, minute, 0)
        
        # True Solar Time Calculation
        if longitude is not None:
            # 1. Longitude Correction: 4 minutes per degree difference from TZ meridian
            # TZ Meridian = tz_offset * 15
            tz_meridian = tz_offset * 15.0
            long_diff = longitude - tz_meridian
            geo_correction = long_diff * 4 # minutes
            
            # 2. Equation of Time (EOT) Approximation
            # d = number of days since start of year
            # Simple approximation formula
            date_val = datetime(year, month, day)
            day_of_year = date_val.timetuple().tm_yday
            B = (360 / 365) * (day_of_year - 81) * (math.pi / 180) # Convert to radians
            eot = 9.87 * math.sin(2*B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)
            
            total_adjust_minutes = geo_correction + eot
            
            # Adjust time
            adj_time = date_val + timedelta(hours=hour, minutes=minute) + timedelta(minutes=total_adjust_minutes)
            
            # Recreate Solar object with True Solar Time
            # Note: Lunar library might handle this differently, but for Bazi, we feed the adjusted time.
            self.solar = Solar.fromYmdHms(adj_time.year, adj_time.month, adj_time.day, adj_time.hour, adj_time.minute, adj_time.second)
            self.is_true_solar = True
            self.adjust_minutes = total_adjust_minutes
            
        else:
            self.solar = self.solar_raw
            self.is_true_solar = False
            self.adjust_minutes = 0

        self.lunar = self.solar.getLunar()
        self.bazi = self.lunar.getEightChar()

    def get_chart(self):
        return {
            "year": {
                "stem": str(self.bazi.getYearGan()),
                "branch": str(self.bazi.getYearZhi()),
                "hidden_stems": [str(g) for g in self.bazi.getYearHideGan()]
            },
            "month": {
                "stem": str(self.bazi.getMonthGan()),
                "branch": str(self.bazi.getMonthZhi()),
                "hidden_stems": [str(g) for g in self.bazi.getMonthHideGan()]
            },
            "day": {
                "stem": str(self.bazi.getDayGan()),
                "branch": str(self.bazi.getDayZhi()),
                "hidden_stems": [str(g) for g in self.bazi.getDayHideGan()]
            },
            "hour": {
                "stem": str(self.bazi.getTimeGan()),
                "branch": str(self.bazi.getTimeZhi()),
                "hidden_stems": [str(g) for g in self.bazi.getTimeHideGan()]
            },
            "meta": {
                "is_true_solar_time": self.is_true_solar,
                "time_adjustment_min": self.adjust_minutes
            }
        }

    def get_wuxing_counts(self):
        # Calculate approximate Five Elements strength based on simple count
        # This is a naive implementation; a full one would consider season, hidden stems, etc.
        elements = {
            "Jin": 0, # Metal
            "Mu": 0,  # Wood
            "Shui": 0, # Water
            "Huo": 0,  # Fire
            "Tu": 0   # Earth
        }
        return {}

    def get_details(self):
        return {
            "lunar_date": self.lunar.toString(),
            "solar_date": self.solar.toString(),
            "jie_qi": self.lunar.getJieQi(),
        }

    def get_luck_cycles(self, gender_idx):
        """
        gender_idx: 1 for Male, 0 for Female
        Returns a list of Da Yun cycles.
        """
        yun = self.bazi.getYun(gender_idx)
        da_yun_arr = yun.getDaYun()
        
        cycles = []
        # Generally we care about the 10-year cycles (starting from index 1 usually, index 0 is pre-luck)
        # But let's return all valid ones
        
        for i, dy in enumerate(da_yun_arr):
            start_year = dy.getStartYear()
            age = dy.getStartAge()
            gan_zhi = dy.getGanZhi()
            
            if i == 0 and not gan_zhi:
                continue # Skip empty pre-luck placeholder if any
                
            cycles.append({
                "index": i,
                "start_year": start_year,
                "end_year": start_year + 9,
                "start_age": age,
                "gan_zhi": gan_zhi,
                "gan": gan_zhi[0] if gan_zhi else "",
                "branch": gan_zhi[1] if gan_zhi else ""
            })
            
        return cycles
