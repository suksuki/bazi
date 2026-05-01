# V20 I18N Terminology

V20 now separates deterministic multilingual terminology from LLM rendering.

## Deterministic Locales

`v20.i18n.terminology` owns the baseline domain and section terms for:

- `zh`
- `en`
- `ko`

The answer composer uses these maps for English and Korean so localized output
does not leak Chinese section bodies or internal ids.

## LLM Boundary

LLM multilingual rendering remains a bounded rewrite task. It may improve tone
later, but it must start from the deterministic localized answer and pass the
same hard safety validator.
