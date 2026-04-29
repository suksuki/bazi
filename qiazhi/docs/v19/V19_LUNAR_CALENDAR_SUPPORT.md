# V19 Lunar Calendar Support

## Goal

V19 should accept both solar and lunar birth input, matching the V17 user-facing behavior.

## Behavior

When `birth_input.calendar_type` or `birth_input.calendar` is `lunar`, V19 converts the lunar date to a solar date before running the existing chart structure engine.

Leap lunar month is supported through:

```json
{
  "calendar_type": "lunar",
  "lunar_is_leap_month": true
}
```

The conversion follows the V17 convention:

- normal lunar month: `month`
- leap lunar month: negative `month`
- conversion library: `lunar_python`

Runtime dependency:

```bash
python3 -m pip install lunar-python
```

## Output Contract

The original input is preserved in:

```text
data.birth_input
```

The converted solar input is exposed in:

```text
data.birth_input_solar
```

Conversion metadata is exposed in:

```text
data.calendar_conversion
chart.calendar_conversion
```

## Boundary

This change only normalizes calendar input.

It does not change:

- `income_stability`
- guided question ranking
- Rule DB signal logic
- prediction boundaries

V19 still uses the current V19 chart structure algorithm after conversion, including the existing approximate solar-term boundary note.
