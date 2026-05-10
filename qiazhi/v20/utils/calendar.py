from __future__ import annotations

import logging

from lunar_python import Lunar, Solar

from v20.ops.logging import get_logger, log_event


LOGGER = get_logger("v20.calendar")


def resolve_pillars(
    year_str: str,
    month_str: str,
    day_str: str,
    hour_str: str,
    calendar: str = "solar",
    gender: str = "male",
    lunar_is_leap: bool = False,
) -> dict[str, str]:
    """
    Resolve birth date into four pillars (年柱, 月柱, 日柱, 时柱).
    
    If all inputs are already 2-character pillars, return as-is.
    If any input is numeric, we assume the user is providing a date and resolve it.
    """
    y_val, m_val, d_val, h_val = str(year_str), str(month_str), str(day_str), str(hour_str)
    
    # Placeholder blacklist
    placeholders = {"甲子", "戊辰", "甲午", "辛酉", "庚子", "乙亥", "辛丑"}
    
    # Check if we need resolution: if any field looks like a number (at least one digit)
    # AND it's not a standard 2-character pillar
    needs_resolution = any(any(c.isdigit() for c in s) for s in [y_val, m_val, d_val, h_val])
    
    if not needs_resolution:
        # If it's already pillars (including placeholders), return as-is
        return {"year": y_val, "month": m_val, "day": d_val, "hour": h_val}

    # Perform resolution
    try:
        def to_int(s):
            d = "".join(filter(str.isdigit, str(s)))
            return int(d) if d else None

        y = to_int(y_val)
        m = to_int(m_val)
        d = to_int(d_val)
        h = to_int(h_val) or 0
        
        # If we have at least YMD, we can resolve
        if y is not None and m is not None and d is not None:
            if calendar == "lunar":
                m_actual = -m if lunar_is_leap else m
                lunar_obj = Lunar.fromYmdHms(y, m_actual, d, h, 0, 0)
            else:
                solar_obj = Solar.fromYmdHms(y, m, d, h, 0, 0)
                lunar_obj = solar_obj.getLunar()
            
            bazi = lunar_obj.getBaZi()
            log_event(
                LOGGER,
                logging.INFO,
                "calendar_resolved",
                event="calendar_resolved",
                calendar=calendar,
                year=y,
                month=m,
                day=d,
                hour=h,
            )
            return {
                "year": bazi[0],
                "month": bazi[1],
                "day": bazi[2],
                "hour": bazi[3],
            }
    except Exception as exc:
        log_event(
            LOGGER,
            logging.WARNING,
            "calendar_resolution_failed",
            event="calendar_resolution_failed",
            calendar=calendar,
            error_type=type(exc).__name__,
        )

    # Fallback: if resolution failed or was incomplete, return as-is
    def clean(s):
        # Allow standard pillars (2 chars, no digits)
        if s and len(s) == 2 and not any(c.isdigit() for c in s):
            return s
        return ""

    return {
        "year": clean(y_val),
        "month": clean(m_val),
        "day": clean(d_val),
        "hour": clean(h_val),
    }


def resolve_luck_pillar(
    year_str: str,
    month_str: str,
    day_str: str,
    hour_str: str,
    calendar: str = "solar",
    gender: str = "male",
    lunar_is_leap: bool = False,
    target_year: int = 2026,
) -> str:
    """
    Calculate the current 大运 (luck pillar) for a given birth date and target year.

    Supports numeric birth dates (1990, 5, 4, 12). Explicit GanZhi pillars
    do not contain enough birth-date information to derive 起运 and return empty.

    gender: 'male' or 'female'
    target_year: the year to check which luck pillar is active
    Returns: the GanZhi string of the active luck pillar (e.g. '辛丑')
    """
    try:
        y_s, m_s, d_s, h_s = str(year_str), str(month_str), str(day_str), str(hour_str)
        y_is_digit = y_s.isdigit()
        m_is_digit = m_s.isdigit()
        d_is_digit = d_s.isdigit()

        if y_is_digit and m_is_digit and d_is_digit:
            # Numeric path: direct resolution
            y, m, d, h = int(y_s), int(m_s), int(d_s), int(h_s) if h_s.isdigit() else 0
            if not all([y, m, d]):
                return ""
        elif len(y_s) == 2 and not y_is_digit:
            # Explicit pillars do not carry enough birth-date information to derive 起运.
            # Keep luck empty unless the caller supplied it explicitly.
            return ""
        else:
            return ""
    except (ValueError, TypeError):
        return ""

    try:
        if calendar == "lunar":
            m_actual = -m if lunar_is_leap else m
            lunar = Lunar.fromYmdHms(y, m_actual, d, h, 0, 0)
        else:
            solar = Solar.fromYmdHms(y, m, d, h, 0, 0)
            lunar = solar.getLunar()

        bazi = lunar.getEightChar()
        # gender: 1=male, 0=female
        gender_code = 1 if gender == "male" else 0
        yun = bazi.getYun(gender_code)

        # Find the active luck pillar for the target year
        luck_pillars = yun.getDaYun()
        matched = ""
        for dy in luck_pillars:
            gz = dy.getGanZhi()
            if not gz:
                continue
            start = dy.getStartYear()
            end = dy.getEndYear()
            if start <= target_year <= end:
                matched = gz
                break

        if not matched and luck_pillars:
            # If target_year is beyond the last luck pillar (e.g., age > 100)
            last_dy = luck_pillars[-1]
            last_gz = last_dy.getGanZhi()
            last_end = last_dy.getEndYear()
            
            if target_year > last_end and last_gz:
                from v20.core.constants import STEMS, BRANCHES
                
                # Determine direction: 1 if forward, -1 if backward
                # We can infer direction by comparing the first and second pillars
                direction = 1
                if len(luck_pillars) > 1:
                    first_gz = luck_pillars[0].getGanZhi()
                    second_gz = luck_pillars[1].getGanZhi()
                    if first_gz and second_gz:
                        idx1 = STEMS.index(first_gz[0])
                        idx2 = STEMS.index(second_gz[0])
                        if (idx2 - idx1) % 10 != 1:
                            direction = -1
                
                # Calculate how many decades past the last end year
                decades_diff = (target_year - last_end - 1) // 10 + 1
                
                s_idx = STEMS.index(last_gz[0])
                b_idx = BRANCHES.index(last_gz[1])
                
                new_s = STEMS[(s_idx + direction * decades_diff) % 10]
                new_b = BRANCHES[(b_idx + direction * decades_diff) % 12]
                matched = f"{new_s}{new_b}"

        return matched
    except Exception as exc:
        log_event(
            LOGGER,
            logging.WARNING,
            "luck_pillar_resolution_failed",
            event="luck_pillar_resolution_failed",
            calendar=calendar,
            error_type=type(exc).__name__,
        )
        return ""


def resolve_target_year(flow_year_pillar: str, birth_year: int = 0) -> int:
    """
    Infers the target year number from a GanZhi flow year pillar.
    If it's numeric, returns it.
    If it's GanZhi, finds the year closest to 'now' that matches it.
    """
    val = str(flow_year_pillar).strip()
    if not val:
        return Solar.fromYmdHms(2026, 1, 1, 0, 0, 0).getYear() # Default for V20 for now
    
    if val.isdigit():
        return int(val)
    
    # If it's GanZhi (2 chars)
    if len(val) == 2:
        from v20.core.constants import STEMS, BRANCHES
        if val[0] in STEMS and val[1] in BRANCHES:
            # Find year matching this GanZhi closest to 2026
            current_y = 2026
            for offset in range(0, 60):
                # Check current_y + offset and current_y - offset
                for y in [current_y + offset, current_y - offset]:
                    if Lunar.fromYmdHms(y, 1, 1, 0, 0, 0).getYearInGanZhi() == val:
                        return y
    
    # Extract digits as fallback
    digits = "".join(filter(str.isdigit, val))
    return int(digits) if digits else 2026
