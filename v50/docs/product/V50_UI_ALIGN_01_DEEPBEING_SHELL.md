# UI-ALIGN-01 DeepBeing Shell

Status: implementation baseline

## Product hierarchy

```text
DeepBeing
|- My Life World
|- Chart Workbench
|  |- Overview
|  |- Structure
|  `- Abu narration
`- Mingli Lab (role disclosed)
```

All three product areas consume one account, Case, canonical scene, navigation state, design system, and data-loading pass. Overview, OneCanvas, and Abu narration are internal Workbench projections, not separate applications.

## Consolidation

- Removed the duplicate page-level header, account context, case context, and top-level surface navigation from the old Experience layout.
- Replaced them with one desktop sidebar, one mobile header, and one mobile bottom navigation.
- Kept one Case selector and one Abu companion for every area.
- Kept one `Promise.allSettled` Case load; switching areas performs no second API load.
- Replaced the accumulated stylesheet with one responsive design system and removed duplicate rules and malformed closing braces.
- Reused the existing server-authorized Canvas projection in Lab; no Lab relation engine or client-side Mingli inference was added.

## Disclosure

- Member views receive structural, time-activated, and effective relations from the server projection.
- Potential relations, hidden-stem nodes, and detailed provenance remain practitioner/Lab disclosures.
- Workbench applies the member-facing Lens even for an authorized admin; opening Lab is the explicit act that reveals the research field.
- The frozen Experience API receives a derived compatibility `role`; `account_role` remains the sole stored authority, so Admin is no longer silently downgraded to the member Canvas projection.
- Product navigation never promotes a relation or writes Chart/LifeCase state.

## Responsive contract

- Desktop uses a stable sidebar and a wide unframed work area.
- Tablet and mobile use a compact top context bar and bottom product navigation.
- The four natal pillars remain a four-column object on 390px.
- The six-pillar relation canvas remains horizontally inspectable with stable semantic slot identity.
- Abu stays above mobile navigation and uses the same narration state in every area. In Workbench and Lab it defaults to the compact avatar so it does not cover pillar controls.

## Browser evidence

- Desktop: 1440 x 1000, no horizontal page overflow.
- Mobile: 390 x 844, fixed bottom navigation and compact Abu, no horizontal page overflow.
- The verified Admin case exposes 91 potential relations and 10 hidden-stem nodes in Lab.
- The same case exposes 1 established generation/control relation and 0 hidden-stem rows in Workbench.
- Browser console: no warnings or errors during World -> Workbench -> Lab navigation.

Screenshots are stored under `reports/ui-align-01/screenshots/` as local review artifacts.
