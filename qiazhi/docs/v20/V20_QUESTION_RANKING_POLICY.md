# V20 Question Ranking Policy

V20 separates question generation from question ranking.

## Contract

`BaziFeature.question_hooks` and applied-domain projection generate the only
valid `QuestionCandidate[]`. A ranking policy may reorder those candidates, but
it cannot create:

- new question keys
- new chart facts
- rule activations
- answer conclusions

## Endpoint

```text
GET /api/v20/questions/ranking-policy
```

Future learning-to-rank work can propose domain or stage weights, but the
proposal must pass synthetic validation, artifact registry review, and decision
registry active iteration before scoped runtime use.
