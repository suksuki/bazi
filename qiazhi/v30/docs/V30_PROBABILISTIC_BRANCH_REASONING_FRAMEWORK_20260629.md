# V30 Probabilistic Branch Reasoning Framework

Updated: 2026-06-29

## Why This Exists

V30 must not force every Bazi judgment into a single absolute verdict. Real Bazi reasoning often has multiple live branches: strength may be close, useful-god strategies may compete, domain outcomes may depend on path activation, and hidden feedback may shift weights.

The correct architecture is not to delete words like "可能", "候选", "分支", or "概率". The correct architecture is to reject empty uncertainty and preserve evidence-bound uncertainty.

## Core Rule

Uncertainty is allowed when it is structured:

- It names the actual candidate branch.
- It carries a confidence, probability, score, rank, or weight.
- It binds to Bazi evidence: day master, month branch, ten-god relation, useful-god strategy, rule match, portrait signal, path, timing layer, or counter-evidence.
- It says what would raise or lower the branch.
- It can become a selectable OptionSet for practitioner mode.

Uncertainty is rejected when it is empty:

- "可能", "大概", "不好说", "仅供参考" without evidence.
- Process filler such as "当前阶段", "后续继续观察", "需要进一步分析".
- A vague hedge used to avoid making a stage-local judgment.

## Model Shape

```text
Deterministic facts
-> Ranked candidate branches
-> Evidence and counter-evidence
-> Branch probability or confidence
-> Central brain arbitration
-> Customer wording
-> Practitioner selectable options
-> Training feedback
```

## LLM Role

LLM may express branch reasoning, but it may not create branches from nothing.

Allowed LLM output:

```json
{
  "candidate_points": [
    {
      "kind": "branch",
      "text": "用神取向有两条分支：土负责承接，火负责温煦；当前土的路径权重更高，因为路径落点更能承接官杀压力。",
      "confidence": 0.72,
      "option_hints": [
        {"label": "土为主", "value": "earth_primary"},
        {"label": "火为辅", "value": "fire_secondary"}
      ],
      "resolution_conditions": ["若时运火势过旺，火分支降权", "若土能承接财官，土分支升权"]
    }
  ]
}
```

Rejected LLM output:

```text
目前还无法定论，后续需要进一步观察，仅供参考。
```

## Central Brain Contract

The central brain must preserve evidence-bound branch signals instead of cleaning them into one fake-certain conclusion.

It may still clean:

- generic filler,
- unsupported hedges,
- unsafe fixed claims,
- chart fact mutation,
- internal diagnostics.

It must preserve:

- ranked candidates,
- confidence/probability,
- counter-evidence,
- resolution conditions,
- practitioner-selectable choices.

## Product UI Contract

Customer UI should keep wording concise:

- show the primary branch first,
- show one or two live alternatives only when meaningful,
- describe what would change the judgment,
- do not overwhelm the user with all internal scores.

Practitioner mode can expose more:

- branch list,
- confidence,
- score breakdown,
- evidence and counter-evidence,
- select / downrank / needs-question actions.

## Role Projection Contract

Branch reasoning is not a single UI. It must be projected by role:

```text
Evidence-bound branches
-> role projection
-> user read-only judgment
-> practitioner selectable calibration
-> central brain belief update
-> training signal
```

Ordinary users:

- see branch reasoning as read-only judgment;
- see the primary or highest-probability branch first;
- may see a small number of meaningful alternatives when they help decision making;
- must not receive select / reject / downrank controls;
- should receive practical wording: what this means, what to notice, what action to take.

Practitioners and admin:

- see all useful branch candidates that pass the evidence gate;
- can select, rank, downrank, reject, mark as needs-question, or add notes;
- feed the central brain by changing belief weights and display priority;
- never mutate deterministic chart facts such as four pillars, calendar conversion, luck-cycle calculation, or raw rule truth.

This is a core product distinction. Branches and probabilities are not noise to delete. They are intelligence material:

- for users, branches become concise guidance;
- for practitioners, branches become an interactive testing and calibration surface.

The UI and API must therefore keep two surfaces separate:

- `stage_points`: page-local read-only judgment points;
- `option_sets`: practitioner/user interaction candidates, with role-specific visibility.

## Training Contract

Training targets branch weights and expression quality only:

- `branch_probability_calibration`
- `candidate_rank_weight`
- `counterevidence_penalty`
- `practitioner_selection_feedback`
- `option_extraction_quality`

Training must never mutate:

- four pillars,
- calendar conversion,
- luck or flow-year facts,
- hidden-factor facts unless user confirmed them.
