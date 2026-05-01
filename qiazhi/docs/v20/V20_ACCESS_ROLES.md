# V20 Access Roles

V20 now defines server-side role projection contracts before adding a full
authentication layer.

## Roles

- `user`: bounded answer, measurement topics, safe questions, portrait
  projection, and prediction policy.
- `analyst`: chart facts, time context, core inference, features, knowledge
  alignment, answer plan, and LLM assist.
- `lab`: analyst data plus chart graph, rule paths, and LLM capability
  contracts for dry-run experiments.
- `admin`: operational and promotion-facing summary fields; secrets and raw
  private feedback stay hidden.

## Endpoints

- `GET /api/v20/access/roles`
- `POST /api/v20/measure/view/{role_key}`

The standard `POST /api/v20/measure` remains the full local runtime envelope for
development. Role views are projected server-side and remove blocked fields
before returning data to the caller.
