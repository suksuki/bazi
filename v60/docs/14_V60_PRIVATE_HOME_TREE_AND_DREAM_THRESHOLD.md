# V60 Private Home Tree And Dream Threshold

Status: `ACTIVE_PRODUCT_CONTRACT`

This contract defines the next visible V60 slice. It separates the viewer's
private life from the continuing Dream world without creating a second Case,
tree engine, graph, router or truth system.

## Product Promise

After login, the viewer first returns to their own life tree. Entering Dream is
an explicit crossing into another continuing life line. Returning home restores
the viewer's observation position; it does not rewind, reset or copy the Dream
world.

```text
login
-> my private life tree
-> enter Abu Dream
-> encounter a canonical synthetic life line
-> observe through Dream / Mingli / Abu / Theater / Lab
-> return to my private life tree
```

## Two Scopes, One Authority Chain

### HOME_CASE

- Source: the signed-in account's active `HUMAN_OWNER` Case.
- Privacy: visible only to that account.
- Purpose: the viewer's persistent life archive and future long-term home.
- Tree: a read-only projection of the current versioned LifeCase, chart,
  CanonicalScene and formal Facts.
- It is never inserted into the pool of Dream encounter subjects.

### DREAM_ENCOUNTER

- Source: the active Encounter's admitted canonical synthetic Actor Case.
- Purpose: playable observation, judgment, waiting, Reveal and reconciliation.
- World time continues independently of whether the viewer is currently
  looking at Home or Dream.
- Its LifeCase, Facts, events and tree state remain separate from HOME_CASE.

Both scopes read the same canonical Mingli authority model. Neither the
frontend nor a presentation unit may merge their source references.

## Five Product Units

Dream is the playable center. The other four units are accountable views of
the currently active life line:

| Unit | Home | Dream |
| --- | --- | --- |
| Dream | explicit threshold into the world | playable Encounter |
| Mingli | viewer's formal chart facts | subject's disclosed formal facts |
| Abu Says | bounded explanation and companionship | bounded guidance |
| Theater | future viewer-owned life scenes | admitted Encounter story |
| Lab | hypotheses and unresolved candidates | subject-scoped candidates |

The first implementation exposes Home and the Dream threshold. It does not
invent Home theater content, private questions or Lab conclusions where no
admitted source exists.

## Navigation And Recovery

- `/experience` defaults to `scope=home` after authentication.
- `scope=dream` is entered only through an explicit user command.
- Browser refresh restores the current scope from the URL and reloads its
  server-owned read model.
- Browser Back crosses the same scope boundary without mutating either Case.
- Returning Home does not close or recreate the current Dream Encounter.
- Entering Dream resumes the current Encounter, or creates the next legal one
  through the existing Dream owner.
- Scope changes never use `localStorage` as a fact source.

## Visual Contract

- Desktop-first, white-based Eastern fairy-tale picture-book direction.
- One approved life-world master remains the visual base while the phenotype
  layer is still bounded.
- Home is quiet, private and spacious. Dream is active and event-bearing.
- Current phenotype values may alter restrained atmosphere and texture only;
  they must remain labelled `VISUAL_METAPHOR_ONLY`.
- No Case name, Case ID or account identity may hard-code a tree appearance.
- Final layered tree phenotype assets remain a replaceable media dependency.
- Mobile composition and multilingual copy are reserved, not implemented in
  this slice.

## Fail-closed Rules

- No active HUMAN_OWNER Case: Home displays a clear unavailable state.
- More than one active HUMAN_OWNER Case without a selection contract: Home
  fails closed rather than guessing.
- Home payload must contain no Encounter, Actor, Question, AnswerSeal, Fruit,
  Reveal or synthetic Case reference.
- Dream payload must continue to use its existing Context disclosure boundary.
- Scope crossing writes no Mingli, World, Story or Dream domain fact.

## Acceptance

1. Login visibly lands on the signed-in viewer's life tree.
2. Home and Dream show different subjects and different Case lineage.
3. Enter Dream resumes the current continuing world.
4. Return Home restores the private life tree without resetting Dream.
5. Refresh restores the selected scope.
6. A process restart preserves both Case identities and Dream progress.
7. Home source refs and Dream source refs do not overlap except for shared
   versioned knowledge authority.
8. Scope changes create no canonical writes.
