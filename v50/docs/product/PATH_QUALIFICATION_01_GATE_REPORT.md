# PATH-QUALIFICATION-01 Gate Report

## Decision

```yaml
PATH_QUALIFICATION_01_DIAGNOSTIC: COMPLETE
PROFESSIONAL_PATH_QUALIFICATION: BLOCKED
LOCAL_GATE_04: NOT_PASSED
committed_PathAssertion: 0
work_path_state: unavailable_unconfirmed
```

This was a read-only diagnosis. It did not call an LLM and did not modify a Case, RelationAssertion, PathAssertion, Prompt, knowledge source, or algorithm.

## Account Reconciliation

| Classification | Count |
| --- | ---: |
| `never_evaluated` | 0 |
| `no_candidate` | 37 |
| `segment_rejected` | 5 |
| `persistence_or_version_failure` | 0 |
| `legacy_unresolved` | 2 |
| `committed` | 0 |
| **Total** | **44** |

All 44 source records contain natural-language work-path text. Thirty-seven stop before a structured candidate exists. Five reach candidate material but fail required node, relation, path-key, qualification, or reference checks. Two stored assertions remain explicitly `legacy_unresolved` because their candidate reference cannot be resolved. There are no committed assertions and no stored RelationAssertions available for a committed segment chain.

## Where The Chain Stops

```text
Natural-language cognition
→ structured PathCandidate: absent for 37
→ segment qualification: rejected for 5
→ historical candidate resolution: unresolved for 2
→ committed PathAssertion: 0
```

The mechanical Path Bridge fixtures prove that valid structured inputs can traverse the contract. They do not provide the professional evidence needed to decide which path is the correct work path for a real Case. Producing at least one path was deliberately not used as a success criterion.

## Evidence Boundary

- Engineering gaps: missing structured candidate payloads, missing stable node/relation chains, and two unresolved historical references.
- Professional decision gaps: selecting a principal work path, validating segment direction and meaning, and resolving competing interpretations.
- Forbidden shortcut: parsing prose in Dream or OneCanvas and guessing lines.
- Minimum future candidate: generate a structured candidate against a server-issued relation pool, validate each segment independently, and keep the result non-committed until professional review. This requires separate Owner authorization.

## Reproduction

```text
PYTHONPATH=packages:apps python scripts/v50_audit_path_qualification_01.py
```

Artifacts are written under `.runtime/path-qualification-01`:

- Source Case payload SHA-256: `685e2019740bd134e6eb3976ad282d26235478c8f362cb6725a76875424d233f`
- Summary SHA-256: `ed0f8789e4c3e26cdeaed4e721dc736f2878ec754b52a32272f66da021b3cb68`
- Database Schema observed: `v50.consolidated.003`
- Writes performed: `false`
