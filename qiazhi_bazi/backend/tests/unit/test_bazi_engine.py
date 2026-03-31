from app.services.bazi_engine import get_bazi


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
