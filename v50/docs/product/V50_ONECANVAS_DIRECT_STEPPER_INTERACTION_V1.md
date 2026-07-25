# V50 OneCanvas Direct Stepper Interaction v1

Status: implementation baseline  
Scope: R1 product hardening only  
Date: 2026-07-19

## 1. Product Decision

OneCanvas uses direct manipulation. The visible six pillars are the controls and the result.

```text
Select a glyph
-> reveal previous / next controls on that glyph
-> choose once
-> server compiles a complete legal chart variant
-> all affected pillars, relations and luck periods update in place
```

There is no separate edit mode, candidate panel, preview page or confirmation step. Undo, redo and restore-formal are the correction model.

The first structural edit automatically creates a local Sandbox snapshot. It never writes to ChartVersion or LifeCase.

## 2. The Ten Direct Controls

The ten non-annual glyphs remain visually operable, but their authority differs.

| Visible glyphs | Direct operation | Authoritative meaning |
| --- | --- | --- |
| Natal year stem / branch | previous or next | Move through the complete 60 Jiazi year-pillar cycle |
| Natal month stem / branch | previous or next | Move through the 12 month pillars legal under the selected year stem |
| Natal day stem / branch | previous or next | Move through the complete 60 Jiazi day-pillar cycle |
| Natal hour stem / branch | previous or next | Move through the 12 hour pillars legal under the selected day stem |
| Luck stem / branch | previous or next | Observe the previous or next item in the derived luck sequence; never edit luck |

The annual stem and branch share a separate Gregorian-year stepper:

```text
2026 -> 2027
Gregorian year is selected
Ganzhi is derived
```

## 3. Whole-Pillar Constraint

A glyph step is a compact gesture, not a character mutation.

Example:

```text
甲子 year pillar
tap next on 甲 or 子
-> 乙丑
```

The system must never create `乙子`. Yin stems pair only with yin branches and yang stems pair only with yang branches because the selected result always comes from an authoritative Jiazi family.

The same rule applies to every natal control:

```text
year changed -> preserve the month branch where possible, recompute its legal month stem
day changed  -> preserve the hour branch where possible, recompute its legal hour stem
month changed -> select only from the year-constrained month family
hour changed  -> select only from the day-constrained hour family
```

After a legal four-pillar result is selected, the server recompiles ten gods, hidden stems, relations, timing and the derived luck sequence.

## 4. Birth-Year Anchor

The year pillar has two distinct responsibilities that must not be collapsed:

```text
Ganzhi year pillar -> structural identity, polarity and DaYun direction inputs
Gregorian birth year -> temporal anchor used to locate the current DaYun period
```

A structural Sandbox may step through all 60 Jiazi without a Gregorian anchor. That is valid for observing structure, but it cannot claim which DaYun is current.

The product therefore places a compact Gregorian-year selector beside the year-pillar title. A formal profile supplies it automatically when disclosure is permitted. A chart-only entry shows only Gregorian years compatible with the current Jiazi year pillar; free text and incompatible years are impossible.

Selecting an anchor applies immediately and recompiles the current four pillars. If gender is not yet known, the anchor is retained but no DaYun is inferred. Once gender is selected, the server resolves the sequence and attempts to locate the current period.

If the current chart has a known Gregorian birth-year anchor, stepping the year pillar by one Jiazi also moves the anchor by one Gregorian year when that pair remains calendar-compatible. The server then uses the full four pillars, gender and birth year to locate the observed luck period.

If no birth-year anchor exists, the system may derive the luck direction and sequence after gender is known, but it must state that the current luck period is not located. It must not guess.

## 5. Interaction Language

### Desktop

- Hover or keyboard-focus reveals two small chevrons around the current glyph.
- Selecting a glyph keeps the chevrons visible.
- One click applies one legal step immediately.
- A short in-place status line explains linked changes.

### Touch devices

- First tap selects one glyph and reveals its two 44 px controls.
- Second tap on a chevron applies one legal step immediately.
- Only the selected glyph shows controls, preventing twelve controls from filling the screen.
- The six-pillar geometry does not move when controls appear.

### Feedback

During compilation, the selected glyph breathes softly and controls are disabled. On success, affected nodes transition in place. A compact message distinguishes:

```text
you changed
system linked
luck recalculated and changed
luck recalculated but unchanged
luck unavailable because an input is missing
```

## 6. UI Reduction

The default surface keeps only:

```text
formal / sandbox authority status
gender
Li-Xiang expression control
time playback
undo / redo / restore
six pillars
one compact path command
one contextual status sentence
```

Remove from the default surface:

```text
formal / experiment mode switch
create-experiment command
candidate dropdown panel
preview and apply chain
permanent four-cell status rail
permanent A/B snapshot controls
engineering phase names
long operational instructions
always-visible temporal stage track
```

The capabilities may remain behind internal fixtures, but they do not compete with the six pillars on the primary product surface.

## 7. Authority Invariants

```text
Frontend never assembles a pillar.
Frontend never calculates Five Tigers or Five Rats.
Frontend never edits luck pillars.
Frontend never derives annual Ganzhi from a typed character.
Every natal step selects one server-authorized full-pillar candidate.
Every structural result is recompiled by the existing server compiler.
Formal ChartVersion and LifeCase remain immutable.
Unknown gender never produces a guessed luck sequence.
```

## 8. Multi-Dimensional Display Status

The current OneCanvas has a valid shared-scene foundation for:

```text
Li: structural glyphs and the committed path
Xiang: continuous visual mapping of the same semantic nodes
Shi: playback over the same nodes
Path: committed path and user draft in one space
```

The following dimensions are not yet product-complete and must not be implied by decorative UI:

```text
complete relation lenses
root and reveal lens
temporal activation provenance
relation school profiles
multi-relation coexistence
whole-path validation
role-specific disclosure of advanced lenses
```

These belong to Relation Atlas and later product review. They do not block the direct-control simplification.

Analyst input is useful after this slice for one focused decision: which relation dimensions should be visible by default for Member, Practitioner and Research roles. The analyst is not needed to approve the already deterministic Jiazi stepping contract.

## 9. Acceptance Gate

```text
1. No user path can render an invalid stem-branch pair.
2. Year and day stepping uses 60 complete Jiazi candidates.
3. Month and hour stepping uses 12 dependency-constrained candidates.
4. The first edit creates a Sandbox automatically.
5. One click produces the complete new six-pillar result without confirmation.
6. Luck controls only change observation within the derived sequence.
7. Annual controls change Gregorian year and display derived Ganzhi.
8. Desktop controls appear on hover/focus; mobile shows controls only for the selected node.
9. The layout does not shift when controls appear or compilation completes.
10. Undo, redo and restore-formal remain available and reliable.
```

## 10. Implementation Evidence

```yaml
implementation: COMPLETE
machine_gate: PASS
product_human_gate: PENDING
production_deployment: NOT_REQUESTED

focused_onecanvas_tests: 48_passed
full_regression: 377_passed
javascript_syntax: PASS

playwright_viewports:
  desktop_1440: PASS
  tablet_768: PASS
  mobile_390: PASS
  horizontal_overflow: false

live_interaction_probe:
  gender_compile_http: 200
  source_year_pillar: 庚寅
  stepped_year_pillar: 辛卯
  linked_month_before: 丁亥
  linked_month_after: 己亥
  formal_state_mutated: false
  sandbox_created_automatically: true
  annual_gregorian_step: PASS
```

The machine gate proves legality, authority and rendering continuity. It does
not replace the planned unguided analyst and first-time-user product review.

## 11. Focused Analyst Review Request

The next analyst review should not reopen Jiazi stepping or calendar authority.
It should answer only the unresolved multi-dimensional product questions:

```text
1. Which relation lens is the default for Member, Practitioner and Research?
2. Which dimensions remain on demand: relations, root/reveal, timing activation,
   evidence provenance and competing paths?
3. What is the smallest default scene that explains a chart without becoming a
   spider web?
4. Which relation states require distinct visual language rather than color only?
5. At what role boundary may candidate or school-specific relations be disclosed?
```

The current recommendation is:

```text
Member: committed path + the one relation currently being explained
Practitioner: relation layers + root/reveal + timing activation on demand
Research: full provenance, competing relations, school profile and rejection state
```

This recommendation remains a product candidate until analyst review. It does
not authorize Relation Atlas implementation inside R1.
