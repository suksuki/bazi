from app.schemas.bazi_metadata import FourPillars, PhysicalScanner, StemBranchPair


def _pillars(y: str, m: str, d: str, h: str) -> FourPillars:
    return FourPillars(
        year=StemBranchPair(stem="甲", branch=y),
        month=StemBranchPair(stem="丙", branch=m),
        day=StemBranchPair(stem="戊", branch=d),
        hour=StemBranchPair(stem="庚", branch=h),
    )


def test_physical_scanner_detects_six_clash():
    scanner = PhysicalScanner()
    matrix = scanner.scan(_pillars("申", "寅", "午", "子"))
    details = [p.detail for p in matrix.points]
    assert "寅申冲" in details
    assert "子午冲" in details


def test_physical_scanner_detects_six_combine():
    scanner = PhysicalScanner()
    matrix = scanner.scan(_pillars("子", "丑", "寅", "亥"))
    details = [p.detail for p in matrix.points]
    assert "子丑合" in details
    assert "寅亥合" in details
