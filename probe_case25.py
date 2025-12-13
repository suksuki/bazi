from core.calculator import BaziCalculator
import datetime

def find_date():
    # Year: 1988 (Wu Chen - 戊辰)
    start_date = datetime.date(1988, 6, 1)
    end_date = datetime.date(1988, 7, 31)
    
    target_day_ganzhi = "戊戌"
    
    current = start_date
    while current <= end_date:
        # We need to instantiate BaziCalculator to get the day pillar
        # Assuming hour doesn't change day pillar (mostly true strictly speaking for solar day)
        c = BaziCalculator(current.year, current.month, current.day, 2, 0) # 2 AM for Gui Chou
        chart = c.get_chart()
        
        y_p = f"{chart['year']['stem']}{chart['year']['branch']}"
        m_p = f"{chart['month']['stem']}{chart['month']['branch']}"
        d_p = f"{chart['day']['stem']}{chart['day']['branch']}"
        h_p = f"{chart['hour']['stem']}{chart['hour']['branch']}"
        
        # We want Wu Chen, Wu Wu, Wu Xu, Gui Chou
        # 1988 is Wu Chen.
        # June/July is likely Wu Wu or Ji Wei.
        
        if d_p == "戊戌":
            print(f"Found: {current} -> {y_p} {m_p} {d_p} {h_p}")
            if y_p == "戊辰" and m_p == "戊午" and h_p == "癸丑":
                print("MATCH!")
                return
        
        current += datetime.timedelta(days=1)

if __name__ == "__main__":
    find_date()
