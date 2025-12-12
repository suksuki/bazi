# Engineering Standards & Workflow Guide

## 1. Development Lifecycle (The "Protocol")
All new features and refactors must strictly follow this pipeline:

1.  **Requirement Analysis**: Clear definition of "What" and "Why".
2.  **Technical Design (RFC)**:
    -   Update `implementation_plan.md`.
    -   Discuss changes in `task.md`.
    -   Identify impacts on existing system.
3.  **Test Planning (TDD-First)**:
    -   **MUST** write or specify Automated Tests *before* or *during* implementation.
    -   Define Success Criteria (e.g., "Function returns X", "Latency < 200ms").
4.  **Implementation**: Coding.
5.  **Verification**:
    -   Run Automated Tests (`pytest`).
    -   Manual Validation (if UI).
    -   Update Documentation.

## 2. Documentation Management (`docs/`)
-   `docs/architecture/`: System design, relationships (Mermaid diagrams).
-   `docs/api/`: Function signatures, class contracts.
-   `docs/user_guide/`: Manuals for end-users.
-   `docs/dev/`: Guides for contributors.

## 3. Testing Strategy (`tests/`)
We use `pytest` for all automation.

-   `tests/unit/`: Test individual functions/classes in isolation. **Mock all external calls.**
-   `tests/integration/`: Test interactions between modules.
-   `tests/regression/`: Re-test fixed bugs.
