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
-> optionally carry one private reality question into an exact-domain life
-> encounter a canonical synthetic life line
-> observe through Dream / Mingli / Abu / Theater / Lab
-> leave one private reality observation and later self-report
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
- A Dream private inquiry may bind this Case, its current LifeCase revision
  and Reading for provenance. The inquiry remains in the account-private
  Dream ledger and does not become a Home-tree organ, Fact or Reading.

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

The current implementation exposes Home, the Dream threshold and an optional
account-private reality-question loop inside Dream. It does not invent Home
theater content, write the question into the Home tree or create Lab
conclusions where no admitted source exists.

## Private Question And Reality Follow-Up

- The viewer chooses `career`, `wealth` or `relationship` and writes one
  normalized 4–120 character question.
- The server binds it only to the Grove candidate with that exact domain.
  Matching does not parse the text, use the Reading, reorder candidates or
  substitute another life when the matching story is terminal.
- Inquiry and Encounter are committed atomically. The private record binds the
  account, active Owner Case, LifeCase revision, current Reading, candidate,
  Actor, Tree and Encounter.
- The Dream Encounter remains independent. Its authored Question, AnswerSeal,
  NPC choice and World outcome do not answer or adapt to the private question.
- After completion and reconciliation, three server-issued domain observation
  options become available. Selecting one saves a private task with a
  seven-day checkpoint.
- After returning to the Grove, the viewer may append short self-reported
  check-ins. They are not automatically compared with the Dream result and
  cannot validate Dream or Mingli.
- Starting another private question appends a superseding inquiry; prior
  records are preserved. A task with no check-in or a latest
  `STILL_OBSERVING` report remains visible and blocks supersession until the
  viewer records a final observed/not-observed state.

## Navigation And Recovery

- `/experience` defaults to `scope=home` after authentication.
- `scope=dream` is entered only through an explicit user command.
- Browser refresh restores the current scope from the URL and reloads its
  server-owned read model.
- Browser Back crosses the same scope boundary without mutating either Case.
- Returning Home does not close or recreate the current Dream Encounter.
- Entering Dream resumes the current Encounter, or creates the next legal one
  through the existing Dream owner.
- Submitted private inquiries, selected observations and check-ins reload from
  PostgreSQL. An unsubmitted text draft is not canonical state.
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
- A private inquiry whose domain does not equal the selected Grove candidate
  fails closed.
- A terminal matching candidate is shown as unavailable; the system does not
  redirect the question to another domain.
- A reality-observation option must be server-issued and may be selected only
  after the exact Encounter is completed and reconciled.
- A check-in may be appended only for the authenticated account's latest
  inquiry after its canonical Dream timeline has returned to the Grove,
  including when the source Encounter continued into another chapter first.
- Inquiry, observation and check-in remain `NOT_MINGLI_EVIDENCE` and permit no
  Reading, Decision or Knowledge write. The inquiry uses the selected
  canonical chapter's normal Opportunity/Encounter creation, but its private
  text cannot alter the Episode Question, NPC choice or World outcome.

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
9. Exact-domain inquiry creation and Encounter creation are atomic.
10. The private question remains visible through its bound Encounter without
    changing the authored Dream question or outcome.
11. A completed journey exposes exactly three server-issued reality
    observations and preserves one selected seven-day task.
12. Grove reload restores the latest task and all appended check-in lineage.
13. No private question, task or check-in appears as a Home-tree fact or
    Mingli evidence.
