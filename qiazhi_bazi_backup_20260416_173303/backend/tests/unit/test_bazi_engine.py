from app.services.bazi_engine import get_bazi, get_timeline_snapshot


def test_get_bazi_returns_four_pillars():
    pillars = get_bazi("1977-05-08", "18:00")
    assert pillars.year.stem
    assert pillars.month.branch
    assert pillars.day.stem
    assert pillars.hour.branch


def test_get_bazi_sample_case_matches_expected():
    pillars = get_bazi("1977-05-08", "18:00", "solar")
    assert f"{pillars.year.stem}{pillars.year.branch}" == "丁巳"
    assert f"{pillars.month.stem}{pillars.month.branch}" == "乙巳"
    assert f"{pillars.day.stem}{pillars.day.branch}" == "乙丑"
    assert f"{pillars.hour.stem}{pillars.hour.branch}" == "乙酉"


def test_get_timeline_snapshot_respects_reference_year():
    y2020 = get_timeline_snapshot("1990-01-01", "12:00", "solar", 1, 2020)
    y2026 = get_timeline_snapshot("1990-01-01", "12:00", "solar", 1, 2026)
    assert "dayun" in y2020 and "liunian" in y2020
    assert y2020["liunian"] != y2026["liunian"]


def test_get_bazi_accepts_slash_date_and_seconds_time():
    a = get_bazi("1977/05/08", "18:00:00", "Solar")
    b = get_bazi("1977-05-08", "18:00", "solar")
    assert f"{a.year.stem}{a.year.branch}" == f"{b.year.stem}{b.year.branch}"
    assert f"{a.month.stem}{a.month.branch}" == f"{b.month.stem}{b.month.branch}"


def test_get_bazi_rejects_bad_formats():
    try:
        get_bazi("1977-5-8", "18", "solar")
    except ValueError as exc:
        msg = str(exc)
        assert "YYYY-MM-DD" in msg or "HH:MM" in msg
    else:
        raise AssertionError("expected ValueError for bad date/time format")
