# V60 Media Library

The V60 Media Library preserves generated source material, postprocess lineage,
review evidence, Runtime deliveries and audio/visual cue bindings.

```text
Gemini request
-> immutable source
-> source QA
-> clean/transparent master
-> review artifacts
-> Owner approval
-> Runtime asset registry
-> Cue Bundle
```

`media/catalog.json` is the production-lineage catalog.
`assets/registry.json` is its Runtime release projection. Product components
must read only Runtime assets, never source or review directories.
The complete production contract is
[`docs/08_V60_MEDIA_LIBRARY_AND_PRODUCTION_PIPELINE.md`](../docs/08_V60_MEDIA_LIBRARY_AND_PRODUCTION_PIPELINE.md).

The next approved Gemini production requests are indexed in
[`prompts/V60_NEXT_MEDIA_GENERATION_PACK_V1.md`](prompts/V60_NEXT_MEDIA_GENERATION_PACK_V1.md).

Directory roles:

```text
media/sources/    immutable original files and ingest receipts
media/masters/    clean, lossless or high-quality postprocess masters
media/manifests/  exact processing and imported lineage manifests
media/review/     checkerboards, contact sheets and handoff previews
media/prompts/    versioned Gemini requests and templates
media/jobs/       declarative postprocess jobs
media/schemas/    machine-readable catalog contracts
web/public/assets Runtime-published delivery files
```

Verify everything:

```bash
.venv/bin/python tools/verify_media_library.py
.venv/bin/python tools/audit_media_technical_contracts.py
.venv/bin/python tools/sync_asset_registry.py
```

Ingest a new source without publishing it:

```bash
.venv/bin/python tools/ingest_media_source.py \
  --media-id ABU_04_EXAMPLE \
  --revision v1 \
  --kind ACTOR_MOTION \
  --source /absolute/path/source.mp4 \
  --generator Gemini \
  --prompt-ref media/prompts/ABU_04_EXAMPLE_V1.md \
  --authorization OWNER_APPROVED_GENERATED_SOURCE
```

An existing revision may never be replaced by a different hash. A changed
source must become `v2`, `v3`, and so on.
