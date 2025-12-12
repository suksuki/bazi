# Antigravity Project Roadmap & To-Do List

## 🟢 Status: V2.4 Stable (Quantum Engine Era)
**Last Updated**: 2025-12-13

---

## 🚀 Immediate Priorities (P0)

- [x] **Core Stability**: Fix `BaziCalculator` object/string return types for robust library compatibility. (Completed V2.4)
- [x] **Smart Dashboard**: Implement fully dynamic "Flux -> Quantum" pipeline with Time Machine. (Completed V2.4)
- [x] **Visualization**: Add 12-Year Destiny Wavefunction (Zeitgeist Cinema) to end-user dashboard. (Completed V2.4)
- [x] **Testing**: Establish `tests/test_v2_4_system.py` for end-to-end regression testing. (Completed)

---

## 🔮 Next Major Version (V3.0 "Harmonics")

### 1. Complex Interactions (Na Yin & He Hua)
- [ ] **Na Yin (Melodic Elements)**: Implement 60-Jiazi sound physics (Metal Sound, Fire Sound) to add "Texture" to the energy.
- [ ] **He Hua (Transformation)**: Implement Stem Combination (e.g. Jia-Ji combines to Earth) logic in `FluxEngine`.
    - *Challenge*: Dynamic transformation based on Month Branch support.

### 2. Deep Mining & Learning
- [ ] **Video Learning Pipeline**: Stabilize the Youtube miner to automatically extracting cases from video subtitles.
- [ ] **Feedback Loop**: Allow users to click "Correct/Incorrect" on predictions to auto-tune weight parameters (`golden_parameters.json`).

### 3. User Experience
- [ ] **Export Report**: Generate a PDF/Image summary of the Destiny Chart.
- [ ] **Mobile Optimization**: Adjust Plotly charts for vertical mobile screens.

---

## 🐛 Known Issues / Technical Debt

- **Legacy Code**: Some V1.0 files (`alchemy.py`, etc.) are still in `core/` but unused. Need cleanup.
- **Dependencies**: `lunar_python` version consistency check.
- **Performance**: FluxEngine re-initialization inside 12-year loop (12x overhead). Can optimize by cloning state.

---

## 📂 Documentation Manifest
- `docs/ALGORITHM_CONSTITUTION_v1.0.md`: Core Physics Axioms.
- `docs/PROJECT_HANDOVER_V2.4.md`: Technical Architecture & API.
- `docs/golden_parameters.json`: The "Brain" (Weights & K-Factors).
