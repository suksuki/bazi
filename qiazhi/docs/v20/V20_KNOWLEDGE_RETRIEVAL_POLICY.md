# V20 Knowledge Retrieval Policy

V20 separates reviewed knowledge recall from retrieval ranking.

## Contract

`KnowledgeUnit.status == reviewed` remains the hard gate. Retrieval policy can
reorder reviewed units by domain or tag weight, but it cannot:

- activate rules
- mark unreviewed knowledge as usable
- create chart facts
- create answer conclusions

## Endpoint

```text
GET /api/v20/knowledge/retrieval-policy
```

Future embedding recall and retrieval learning can propose weights, but every
proposal must pass reviewed-status filtering, synthetic validation, artifact
registry review, and decision registry active iteration before scoped runtime use.
