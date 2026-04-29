# V19 P6 Completion Notes

P6 goal: make guided answers rely on structure knowledge and auditable question contracts, while keeping `income_stability` unchanged.

## Completed scope

- Runtime knowledge seed expansion for structure concepts, time-boundary explanations, and answer-expression guidance.
- Knowledge draft seed expansion for analyst review and future Rule DB proposal workflows.
- Guided answer rewrite now receives `knowledge_context` and is instructed to use it as wording/evidence context only.
- Knowledge retrieval now recognizes month command, day master, hidden stems, ten-god metadata, wealth-star boundary, vaults, branch relations, time context, and unsupported-question wording.
- Structural guided-question registry expanded for month command, ten-god metadata, element relation, vault structure, and income path structure.
- Frontend fallback question library and label contract updated for the new P6 questions.
- User-facing guidance copy simplified from mechanical agent wording to plain navigation.
- Guided-question audit matrix script added.
- One-shot P6 seed/audit helper added.

## Non-goals

- No direct change to `income_stability` derivation.
- No automatic wealth, health, marriage, or timing prediction.
- No default Rule DB mutation unless `INGEST_RULE_DB=1` is explicitly used in the helper script.

## Deployment checklist

1. Deploy code.
2. Restart V19.
3. Run `./v19/scripts/p6_seed_and_audit.sh` on the server.
4. Review audit failures, if any.
5. Only run with `INGEST_RULE_DB=1` after analyst approval or when explicitly refreshing active Rule DB signals.
