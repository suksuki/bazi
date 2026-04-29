# V19 Profile and Step Flow Scope

Date: 2026-04-29
System: V19 Guided Bazi Agent

## Purpose

V19 user flow is now profile-first and step-based.

```text
Entry
-> Guest trial or Login/Register
-> Bazi Profiles
-> Step 1 Birth Input
-> Step 2 Pillar Confirmation
-> Step 3 Time Selection
-> Step 4 Agent
```

## Entry Simplification

The public entry no longer shows four role cards.

```text
Primary: Guest trial
Secondary: Login / Register
```

Role is resolved after login and controls surfaces only.

```text
admin -> /admin
practitioner -> /profiles plus /lab access
user -> /profiles
visitor guest -> /profiles
```

## Bazi Profile

```ts
type BaziProfile = {
  id: string
  owner_id: string
  name: string
  birth_input: {
    year: number
    month: number
    day: number
    hour: number
    minute: number
    gender: string
    calendar: string
    calendar_type: string
  }
  created_at: string
  updated_at: string
}
```

Profiles are local MVP persistence, stored in V19 runtime files.

## Step Flow

Step 1 Birth Input:

```text
birth fields only
no inference
no LLM
```

Step 2 Pillar Confirmation:

```text
four-pillar confirmation
uses /api/agent/structure
structure preview only
```

Step 3 Time Selection:

```text
luck cycle + flow year context
context only
not prediction
```

Step 4 Agent:

```text
profile summary
question builder
Run Analysis
ResultCard
Time Context collapsed
Evidence collapsed
```

## Boundaries

```text
profile flow does not change inference
profile flow does not change signal output
structure preview does not call LLM
role does not affect analysis
Agent page no longer contains birth input form
```
