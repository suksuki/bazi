from lunar_python import Solar, Lunar, EightChar

# Test Date: 1990-01-01 12:00
solar = Solar.fromYmdHms(1990, 1, 1, 12, 0, 0)
lunar = solar.getLunar()
bazi = lunar.getEightChar()

print(f"Bazi: {bazi}")

# Da Yun
# 1 = Man, 0 = Woman (lunar_python convention might differ, checking docs or trying)
# usually getYun(gender) where gender 1=Male, 0=Female
try:
    yun = bazi.getYun(1) # Male
    print(f"Start Yun: {yun.getStartYear()} / {yun.getStartMonth()}")
    
    da_yun_arr = yun.getDaYun()
    for i, dy in enumerate(da_yun_arr):
        # Index, StartYear, GanZhi
        print(f"Yun {i}: {dy.getStartYear()} age, {dy.getGanZhi()}")
        
        # Liu Nian (Annual Pillar)
        # getLiuNian() returns array of years in this Da Yun
        liu_nian = dy.getLiuNian()
        if i == 0: # Print first Da Yun's years
            for ln in liu_nian:
                print(f"  - {ln.getYear()} ({ln.getAge()} age): {ln.getGanZhi()}")
                
except Exception as e:
    print(f"Error: {e}")
