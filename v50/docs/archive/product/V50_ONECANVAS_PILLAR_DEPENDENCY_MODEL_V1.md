# V50 OneCanvas Pillar Dependency Model v1

> **SUPERSEDED**: this document incorrectly treated month and hour as one
> retained branch plus one automatically derived stem. It is retained only as
> decision history. The governing contract is now
> `V50_ONECANVAS_PILLAR_SELECTION_AND_DAYUN_ALGORITHM_V2.md`.

```yaml
status: SUPERSEDED
scope: R1 pillar selection correction
product_gate: PENDING
full_c2_authorized: false
production_deployment: false
```

## 1. Correction

OneCanvas is a **sexagenary-cycle structural sandbox**, not a nearby-birth-date
search form.

The previous R1 implementation exposed year, month, day and hour as four edit
axes and returned a small set of nearby Gregorian-date candidates. That model
made the interaction harder while obscuring the actual dependency structure.
It is retired for this surface.

The corrected authority model is:

```text
Year pillar:  independent choice from all 60 Jiazi
      ↓
Month pillar: month branch stays at the current semantic month;
              month stem follows the selected year stem (Five Tigers)

Day pillar:   independent choice from all 60 Jiazi
      ↓
Hour pillar:  hour branch stays at the current semantic hour;
              hour stem follows the selected day stem (Five Rats)

Annual pillar: independent observation choice

Luck pillar:  never editable; derived after the natal structural variant
```

## 2. Slot Authority

| Slot | User action | Authority | UI treatment |
| --- | --- | --- | --- |
| Year | choose one of 60 Jiazi | deterministic cycle compiler | full closed select |
| Month | no direct editing | derived from year stem and retained month branch | linked result |
| Day | choose one of 60 Jiazi | deterministic cycle compiler | full closed select |
| Hour | no direct editing | derived from day stem and retained hour branch | linked result |
| Luck | no direct editing | deterministic structural timing compiler | derived result |
| Annual | choose observation year | calendar engine | independent time selector |

Month and hour remain first-class semantic pillars. They are not hidden or
reduced to labels; they are simply not independent choice axes.

## 3. Structural Validity and Calendar Honesty

Every year/day option is a valid member of the 60 Jiazi cycle. Linked month and
hour stems are compiled by the deterministic Five Tigers/Five Rats rules.

This proves **GanZhi dependency validity**. It does not prove that every
structural variant maps to a particular real Gregorian birth datetime.

Therefore the UI and contracts must say:

```text
结构实验 / 六十甲子选择
```

and must not claim:

```text
真实生日候选
附近合法出生日期
```

If a future workflow needs to reverse-search a real date, that is a separate
calendar task with location, timezone, solar-term and date constraints.

## 4. Dependency Rules

### Year to Month

The current month branch is retained. Its stem is derived from the selected
year stem using Five Tigers. The compiler returns the complete month pillar.
The browser never implements this rule.

### Day to Hour

The current hour branch is retained. Its stem is derived from the selected day
stem using Five Rats. The compiler returns the complete hour pillar. The
browser never implements this rule.

### Luck

Luck is calculated only after the natal structural variant is complete.

- A year change may alter direction and the sequence derived from the linked
  month pillar.
- A day change normally leaves the luck sequence unchanged because year and
  month remain unchanged.
- A structural experiment does not invent a real birth date or a new solar-term
  distance. Any inherited temporal anchor or unavailable start-age result must
  be disclosed explicitly.
- `recalculated_changed`, `recalculated_unchanged`, and
  `recalculation_unavailable` remain distinct states.

## 5. Interaction

```text
Click year
→ choose one of 60 Jiazi
→ preview linked month
→ preview derived luck result
→ confirm experiment

Click day
→ choose one of 60 Jiazi
→ preview linked hour
→ preview unchanged/derived luck result
→ confirm experiment

Click month
→ inspect linked result and explanation
→ offer "change year pillar"

Click hour
→ inspect linked result and explanation
→ offer "change day pillar"
```

No free-text input is accepted. A select change is only a preview; confirmation
is explicit. The formal ChartVersion remains immutable.

R1 keeps one structural choice axis active in an experiment at a time. A future
multi-axis sandbox must compile the combined year/day state authoritatively; it
may not merge two precompiled variants in the browser.

## 6. Hard Boundaries

- The frontend does not contain Jiazi, Five Tigers, Five Rats, relation, Graph,
  path or luck algorithms.
- Month and hour cannot be independently edited.
- Luck cannot be manually edited.
- Annual observation cannot modify the natal structural variant.
- Structural candidates remain hypothetical and never write ChartVersion or
  LifeCase.
- Switching the active structural axis must clearly disclose that the prior
  single-axis preview is replaced.
- No LLM, TTS, Reasoner or professional judgment changes are authorized.
- This correction does not authorize R2-R6 or production deployment.

## 7. Machine Gate

The correction passes only when:

1. Year and day each expose all 60 unique Jiazi in canonical order.
2. Every year candidate has the correct linked month stem and retained month
   branch.
3. Every day candidate has the correct linked hour stem and retained hour
   branch.
4. Month and hour are absent from editable candidate families.
5. Luck and annual remain non-editable semantic slots.
6. The frontend contains no dependency calculation.
7. Desktop and 390px mobile complete both selection flows without overflow.
8. The full regression remains green.
