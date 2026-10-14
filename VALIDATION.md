# Validation record

Date: 2026-10-15. Local platform: Windows, Python 3.12.14.

- 29 automated tests passed. Coverage includes exact source evidence, malformed JSON, ambiguous amounts/dates, one-cent arithmetic errors, conflicts, truncated output, optional correction provenance, blocked approvals, stale versions, deduplication, and review/audit transitions.
- One real development model probe followed by 16 real evaluation requests, with raw outputs preserved. The initial probe prompted a generic identifier-copying instruction before the evaluation. No evaluation retries were selected.
- Raw LLM: 0/16 exact records, 109/128 fields, 7/16 routing decisions. Rules: 16/16, 128/128, 16/16 respectively.
- Source correction: 13/16 exact records, 125/128 fields, 16/16 routing decisions, 16 corrected fields. This correction was designed after inspecting raw failures; these are post-hoc diagnostic scores, not held-out validation.
- Published artifacts include the fictional inputs, expected answers, prompt/fixture hashes, runtime reference, raw model outputs, and per-field comparisons. No private inputs or review database are published.

A fresh virtual environment installed the editable package successfully; all 29 tests passed there too. The installed console command extracted the standard fixture using the rules backend. Browser verification covered raw output, optional correction, the seven source-issue cases, arithmetic mismatch routing, and the rules view. The report layout was inspected visually and the browser reported no warning/error logs. GitHub CI status is pending publication.
