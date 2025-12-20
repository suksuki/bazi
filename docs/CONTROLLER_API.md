# BaziController API Reference
## V9.5 MVC Architecture - Official Interface Specification

> **Version:** 9.5.0-MVC  
> **Last Updated:** 2024-12-15  
> **Status:** Production Ready ✅

---

## 📚 Overview

`BaziController` is the **central controller layer** in the V9.5 MVC architecture. It encapsulates all Model interactions and provides a unified API for View components (P1, P2, P3).

### Design Principles

1. **Single Source of Truth**: All business logic flows through the Controller
2. **Lazy Initialization**: Models are only created when needed
3. **State Isolation**: Each Controller instance maintains its own state
4. **Backward Compatibility**: Legacy Engine access preserved for calibration tools

---

## 🔧 Installation & Import

```python
from controllers.bazi_controller import BaziController

# Create controller instance
controller = BaziController()
```

---

## 📦 Public API Methods (20+)

### Category 1: Input Management

#### `set_user_input()`
**Primary entry point for user data.**

```python
controller.set_user_input(
    name: str,              # User's name
    gender: str,            # "男" or "女"
    date_obj: datetime.date, # Birth date
    time_int: int,          # Birth hour (0-23)
    city: str = "Unknown",  # Birth city for GEO correction
    enable_solar: bool = True,  # Enable solar time correction
    longitude: float = 116.46   # Longitude for solar time
) -> None
```

**Example:**
```python
import datetime
controller.set_user_input(
    name="Jack Ma",
    gender="男",
    date_obj=datetime.date(1964, 9, 10),
    time_int=8,
    city="Hangzhou"
)
```

---

### Category 2: Chart & Basic Data Accessors

#### `get_chart()`
Returns the calculated Bazi chart.

```python
chart = controller.get_chart()
# Returns: Dict with 'year', 'month', 'day', 'hour' pillars
```

#### `get_details()`
Returns calculation details.

```python
details = controller.get_details()
# Returns: Dict with calculation metadata
```

#### `get_luck_cycles()`
Returns the Da Yun (Great Luck) cycles list.

```python
cycles = controller.get_luck_cycles()
# Returns: List[Dict] - Each dict contains luck cycle info
```

#### `get_calculator()`
Returns the BaziCalculator instance (for advanced usage).

```python
calc = controller.get_calculator()
# Returns: Optional[BaziCalculator]
```

---

### Category 3: FluxEngine Interface

#### `get_flux_engine()`
Returns the FluxEngine instance.

```python
flux = controller.get_flux_engine()
# Returns: Optional[FluxEngine]
```

#### `get_flux_data()`
Compute and return flux energy state.

```python
flux_data = controller.get_flux_data(
    selected_yun: Optional[Dict] = None,  # Selected Da Yun dict
    current_gan_zhi: Optional[str] = None # Current Liu Nian GanZhi
)
# Returns: Dict - Flux energy state
```

---

### Category 4: QuantumEngine Interface

#### `get_quantum_engine()`
Returns the QuantumEngine instance.

```python
engine = controller.get_quantum_engine()
# Returns: Optional[QuantumEngine]
```

#### `run_single_year_simulation()`
Run quantum calculation for a single year.

```python
result = controller.run_single_year_simulation(
    case_data: Dict,      # Prepared case data dict
    dynamic_context: Dict # {'year': GanZhi, 'dayun': GanZhi}
)
# Returns: Dict - Quantum engine calculation results
```

#### `run_timeline_simulation()` ⭐
**Core method for multi-year trajectory simulation.**

```python
df, handover_years = controller.run_timeline_simulation(
    start_year: int,              # Starting year
    duration: int = 12,           # Number of years
    case_data: Optional[Dict] = None,  # Pre-built case data
    params: Optional[Dict] = None      # Golden parameters
)
# Returns: Tuple[pd.DataFrame, List[Dict]]
#   - DataFrame: year, career, wealth, relationship, etc.
#   - handover_years: List of luck pillar change events
```

**DataFrame Columns:**
| Column | Description |
|--------|-------------|
| `year` | Year (int) |
| `label` | "YYYY\n干支" formatted label |
| `career` | Career energy score |
| `wealth` | Wealth energy score |
| `relationship` | Relationship energy score |
| `base_career` | Baseline career (without dynamic effects) |
| `is_treasury_open` | Boolean - treasury opening event |
| `treasury_icon` | Icon for treasury events |
| `result` | Full calculation result dict |

---

### Category 5: GEO & Luck Interfaces ⭐

#### `get_geo_modifiers()`
Get geographic correction modifiers.

```python
mods = controller.get_geo_modifiers(
    city: Optional[str] = None  # Target city (uses controller's city if None)
)
# Returns: Dict - GEO modifier coefficients
```

#### `get_luck_timeline()`
Get luck pillar timeline.

```python
timeline = controller.get_luck_timeline(
    num_steps: int = 10  # Number of luck cycles
)
# Returns: List[Dict] - Luck cycle information
```

#### `get_dynamic_luck_pillar()`
Get the active luck pillar for a specific year.

```python
pillar = controller.get_dynamic_luck_pillar(
    year: int  # Target year
)
# Returns: str - Luck pillar GanZhi (e.g., "癸卯")
```

---

### Category 6: P2 Quantum Verification Interface ⭐⭐

**These methods are specifically designed for P2 (Quantum Lab) GEO comparison features.**

#### `get_baseline_trajectory()`
Get energy trajectory **WITHOUT** GEO correction (baseline).

```python
df = controller.get_baseline_trajectory(
    start_year: int,
    duration: int = 12,
    params: Optional[Dict] = None
)
# Returns: pd.DataFrame with columns:
#   - baseline_career, baseline_wealth, baseline_relationship
```

#### `get_geo_trajectory()`
Get energy trajectory **WITH** GEO correction for specified city.

```python
df = controller.get_geo_trajectory(
    city: str,           # Target city
    start_year: int,
    duration: int = 12,
    params: Optional[Dict] = None
)
# Returns: pd.DataFrame with columns:
#   - geo_career, geo_wealth, geo_relationship
```

#### `get_geo_comparison()` ⭐⭐⭐
**The ultimate GEO comparison method - combines baseline and GEO trajectories.**

```python
combined_df, geo_mods = controller.get_geo_comparison(
    city: str,           # Target city
    start_year: int,
    duration: int = 12,
    params: Optional[Dict] = None
)
# Returns: Tuple[pd.DataFrame, Dict]
#   - combined_df: Merged baseline + GEO data
#   - geo_mods: GEO modifier display info
```

**Combined DataFrame Columns:**
| Column | Source |
|--------|--------|
| `year` | Year |
| `label` | Display label |
| `baseline_career` | Neutral location |
| `baseline_wealth` | Neutral location |
| `baseline_relationship` | Neutral location |
| `geo_career` | Target city |
| `geo_wealth` | Target city |
| `geo_relationship` | Target city |

---

### Category 7: Convenience Methods

#### `get_user_data()`
Return current user input data.

```python
data = controller.get_user_data()
# Returns: Dict - Copy of user input
```

#### `get_gender_idx()`
Return gender index (1=male, 0=female).

```python
idx = controller.get_gender_idx()
# Returns: int
```

#### `get_profile()`
Return BaziProfile instance.

```python
profile = controller.get_profile()
# Returns: Optional[BaziProfile]
```

#### `get_wang_shuai_str()`
Calculate Wang/Shuai strength string.

```python
strength = controller.get_wang_shuai_str(
    flux_data: Dict,
    scale: float = 0.08
)
# Returns: str - "身旺", "身弱", or "假从/极弱"
```

---

## 🔌 Integration Patterns

### Pattern A: P1 智能排盘 (Pure View)

```python
from controllers.bazi_controller import BaziController

controller = BaziController()
controller.set_user_input(name, gender, date_obj, time_int, city)

# Get chart for display
chart = controller.get_chart()

# Get timeline simulation
df, handovers = controller.run_timeline_simulation(start_year, 12)

# Render (View responsibility)
render_bazi_chart(chart)
render_energy_curve(df)
```

### Pattern B: P3 命运影院 (Progressive MVC)

```python
from controllers.bazi_controller import BaziController

# Create controller from case data
controller = get_controller_for_case(case_data, city)

if controller:
    # MVC Path: Use Controller API
    combined_df, geo_mods = controller.get_geo_comparison(city, start_year, 12)
    render_hologram(combined_df)
else:
    # Fallback: Direct Engine access
    engine = get_engine()
    # ... legacy logic
```

### Pattern C: P2 量子验证 (Hybrid Mode)

```python
from controllers.bazi_controller import BaziController
from core.engine_v91 import EngineV91 as QuantumEngine

# Controller for standard data access
controller = BaziController()

# Engine for parameter tuning (calibration tool requirement)
engine = QuantumEngine()
engine.update_config(algo_config)
engine.update_full_config(full_algo_config)

# Use Controller for user-facing data
flux_data = controller.get_flux_data()

# Use Engine for batch calibration
for case in cases:
    result = engine.calculate_energy(case_data, dyn_ctx)
```

---

## 📐 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        VIEW LAYER                           │
├─────────────────┬─────────────────┬─────────────────────────┤
│  P1 智能排盘    │  P2 量子验证    │  P3 命运影院            │
│  (Pure View)    │  (Hybrid)       │  (Progressive MVC)      │
└────────┬────────┴────────┬────────┴────────┬────────────────┘
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   CONTROLLER LAYER                          │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              BaziController (20+ Methods)           │   │
│   │  • set_user_input()    • get_geo_comparison()       │   │
│   │  • run_timeline_simulation()  • get_flux_data()     │   │
│   │  • get_baseline_trajectory()  • get_luck_timeline() │   │
│   └─────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      MODEL LAYER                            │
├─────────────────┬─────────────────┬─────────────────────────┤
│ BaziCalculator  │   FluxEngine    │    QuantumEngine V9.1   │
│ (Chart Gen)     │   (Energy)      │    (Spacetime Physics)  │
├─────────────────┴─────────────────┴─────────────────────────┤
│              Sub-Engines: Luck, Treasury, Skull, Harmony    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧪 Testing

### Controller Integration Tests

```bash
# Run all controller tests
pytest tests/integration/test_controller_integration.py -v

# Expected: 15 passed
```

### Test Classes

| Test Class | Coverage |
|------------|----------|
| `TestControllerInitialization` | Version, lazy init |
| `TestUserInputAPI` | Male/female, engine init |
| `TestChartAndLuckAPI` | Chart, luck cycles |
| `TestTimelineSimulation` | F03 curve, handovers |
| `TestGeoComparisonAPI` | F05a dual-curve |
| `TestFluxEngineAPI` | Flux data, Wang Shuai |

---

## 📋 Version History

| Version | Date | Changes |
|---------|------|---------|
| 9.5.0-MVC | 2024-12-15 | Initial MVC architecture release |
| | | - 20+ public methods |
| | | - P2 GEO comparison API |
| | | - P3 progressive decoupling |
| 16.0 | 2024-12-20 | Controller Decomposition Refactor |
| | | - Extracted `InputController` (Validation) |
| | | - Extracted `SimulationController` (Timeline & Caching) |
| | | - Extracted `ConfigController` (Config Management) |
| | | - UI: Modular Tuning Panel with Save support |

---

**© 2024 Bazi Predict System - V9.5 MVC Architecture**
