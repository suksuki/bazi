from lunar_python import Solar, Lunar

solar = Solar.fromYmdHms(2024, 1, 1, 12, 0, 0)
lunar = solar.getLunar()
bazi = lunar.getEightChar()

print("Bazi object dir:", dir(bazi))
print("\nYear Zhi (Branch):", bazi.getYearZhi())
# Check if there's a method on the branch string/object itself or if we need a helper
# In lunar_python, often things return strings.
# Let's check how to get hidden stems.
