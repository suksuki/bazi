import logging
import datetime
from typing import Dict, Any, List, Optional
from lunar_python import Solar
from core.exceptions import BaziInputError

logger = logging.getLogger(__name__)

class InputController:
    """
    Controller responsible for handling, validating, and normalizing user input.
    """

    @staticmethod
    def validate_user_input(name: str, gender: str, date_obj: datetime.date, 
                            time_int: int) -> None:
        """
        Validate basic user input fields.
        
        Raises:
            BaziInputError: If validation fails.
        """
        if not name or not name.strip():
            raise BaziInputError("用户姓名不能为空", "name parameter is empty")
        if gender not in ["男", "女"]:
            raise BaziInputError(f"性别参数无效: {gender}", f"gender must be '男' or '女', got '{gender}'")
        if not isinstance(date_obj, datetime.date):
            raise BaziInputError("日期格式无效", f"date_obj must be datetime.date, got {type(date_obj)}")
        if not (0 <= time_int <= 23):
            raise BaziInputError(f"时间参数无效: {time_int}", "time_int must be between 0 and 23")

    @staticmethod
    def normalize_case_fields(case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure required fields exist in a case dictionary.
        """
        if not isinstance(case, dict):
            return case
        c = case.copy() # Avoid mutating original if possible, though deep copy might be needed for caller
        
        if not c.get("day_master"):
            bazi = c.get("bazi") or []
            if len(bazi) >= 3 and isinstance(bazi[2], str) and bazi[2]:
                c["day_master"] = bazi[2][0]
        if not c.get("gender"):
            c["gender"] = "未知"

        # Reverse lookup birth date/time from full bazi if missing
        if (not c.get("birth_date") or not c.get("birth_time")) and isinstance(c.get("bazi"), list) and len(c["bazi"]) >= 4:
            try:
                dt_val = InputController.reverse_lookup_bazi(c["bazi"])
                if dt_val:
                    c["birth_date"] = dt_val.strftime("%Y-%m-%d")
                    c["birth_time"] = f"{dt_val.hour:02d}:{dt_val.minute:02d}"
            except Exception:
                pass

        # Fill dynamic_checks.year
        if c.get("dynamic_checks"):
            normalized_checks = []
            for chk in c.get("dynamic_checks", []):
                if not isinstance(chk, dict):
                    continue
                chk_copy = chk.copy()
                if "year" not in chk_copy or not chk_copy.get("year"):
                    birth_date = c.get("birth_date")
                    year_val = None
                    if isinstance(birth_date, str) and len(birth_date) >= 4:
                        try:
                            year_val = birth_date.split("-")[0]
                        except Exception:
                            year_val = None
                    if not year_val:
                        bazi = c.get("bazi") or []
                        if len(bazi) >= 1 and isinstance(bazi[0], str) and bazi[0]:
                            year_val = bazi[0]
                    chk_copy["year"] = year_val
                normalized_checks.append(chk_copy)
            c["dynamic_checks"] = normalized_checks
        return c

    @classmethod
    def normalize_cases(cls, cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize a list of cases safely."""
        if not isinstance(cases, list):
            return cases
        return [cls.normalize_case_fields(c) for c in cases]

    @staticmethod
    def reverse_lookup_bazi(target_bazi: List[str], start_year: int = 1950, end_year: int = 2030):
        """
        Brute-force reverse lookup of Bazi (Y, M, D, H GanZhi) to Gregorian datetime.
        Returns datetime.datetime if found, else None.
        """
        if not target_bazi or len(target_bazi) < 4:
            return None
        tg_y, tg_m, tg_d, tg_h = target_bazi[:4]
        
        for y in range(start_year, end_year + 1):
            start_d = datetime.date(y, 1, 1)
            end_d = datetime.date(y, 12, 31)
            curr = start_d
            while curr <= end_d:
                try:
                    s = Solar.fromYmd(curr.year, curr.month, curr.day)
                    l = s.getLunar()
                    if l.getYearInGanZhiExact() != tg_y:
                        curr += datetime.timedelta(days=1)
                        continue
                    if l.getMonthInGanZhiExact() != tg_m:
                        curr += datetime.timedelta(days=1)
                        continue
                    if l.getDayInGanZhiExact() != tg_d:
                        curr += datetime.timedelta(days=1)
                        continue
                    # check hour
                    for h in range(0, 24):
                        sh = Solar.fromYmdHms(curr.year, curr.month, curr.day, h, 0, 0)
                        lh = sh.getLunar()
                        if lh.getTimeInGanZhi() == tg_h:
                            return datetime.datetime(curr.year, curr.month, curr.day, h, 0, 0)
                except Exception:
                    pass
                curr += datetime.timedelta(days=1)
        return None
