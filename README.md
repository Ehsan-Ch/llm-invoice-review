# LLM Invoice Review

A local invoice extraction lab with exact source evidence, decimal arithmetic checks, and a SQLite human review queue. It compares a small language model with a deterministic parser and preserves failures in an interactive report.

**Main finding:** the rules baseline wins on these deliberately structured synthetic invoices. The raw Qwen model changed invoice identifiers; validation caught those changes. This project demonstrates measurement and review controls, not an accuracy claim for production invoice automation.

## Published experiment

16 fictional evaluation invoices, eight fields each; nine should pass the supported checks and seven require review. Model: Qwen3-0.6B Q8_0 through llama.cpp b11617, local CPU inference.

| Method | Exact records | Exact field values | Correct routing |
| --- | ---: | ---: | ---: |
| Raw LLM | 0/16 | 109/128 | 7/16 |
| LLM + optional source correction | 13/16 | 125/128 | 16/16 |
| Rules baseline | 16/16 | 128/128 | 16/16 |

The correction step was developed **after inspecting raw evaluation failures**. Its scores are a diagnostic replay on seen examples, not independent validation. It corrected 16 field values by copying from exact cited source lines and logs every change. Correct routing is not exact extraction accuracy. The raw model passed no invoices, so its zero unsafe passes do not establish useful safety performance.

Median model latency was 9.78 seconds on the recorded CPU. There were no model request errors. Four development fixtures are provided; one was used for a development model probe before the 16-case run. No repeated attempts were selected for the published evaluation. The narrow label templates strongly favor the rules baseline; broader documents and unseen evaluation data are needed before generalizing.

Open [the interactive report](reports/evaluation/report.html) locally, or inspect [the full evaluation JSON](reports/evaluation/evaluation.json). The report switches among methods, filters problematic examples, and shows expected values, source evidence, corrections, and original model output. It is a saved experiment viewer; review decisions use the CLI.

## Install and try without a model

Python 3.11+; no runtime Python dependencies. From the repository root:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e .
.venv\Scripts\invoice-review extract examples/standard.txt --backend rules
.venv\Scripts\invoice-review ingest examples/standard.txt --backend rules
.venv\Scripts\invoice-review list
```

On Linux/macOS use `.venv/bin/python` and `.venv/bin/invoice-review`. The model download helper below is Windows-specific; the Python application is portable.

## Run the local LLM

The optional helper downloads about 660 MB from the official Qwen and llama.cpp repositories, checks pinned SHA-256 hashes, and extracts the runtime inside this repository. Model files are not included in GitHub or the project ZIP.

```powershell
.venv\Scripts\python scripts/setup_windows_model.py
& ./scripts/start_model.ps1
```

Keep that terminal running. In another terminal:

```powershell
.venv\Scripts\invoice-review extract examples/standard.txt
.venv\Scripts\invoice-review extract examples/standard.txt --repair-evidence
.venv\Scripts\invoice-review ingest examples/standard.txt --repair-evidence
```

The endpoint defaults to `http://127.0.0.1:8095` and the model alias to `invoice-qwen`. Only loopback HTTP origins with explicit ports are accepted; redirects and proxies are disabled. Another compatible local server can be selected with global `--endpoint` and `--model` arguments before the command. The setup helper verifies files; an endpoint alias alone does not verify model identity. Published-run provenance is in [runtime-reference.json](runtime-reference.json).

## Human review workflow

Every imported invoice starts `PENDING`, even when validation reports `CHECKS_PASSED`. Copy its full ID and current version from `list`, then record a decision:

```powershell
invoice-review review FULL_ID approve --version 0 --actor reviewer --reason "Checked against the original invoice"
invoice-review audit FULL_ID
invoice-review review FULL_ID reopen --version 1 --actor reviewer --reason "Second review requested"
invoice-review review FULL_ID reject --version 2 --actor reviewer --reason "Source requires correction"
```

Approval requires all implemented checks to pass and revalidates stored evidence. Stale versions are rejected atomically. Reimporting identical normalized text preserves the existing decision and result. Failed records can be rejected; correct their source outside the queue and import the changed text. Reprocessing identical text with a different extraction method requires a separate database, selected with `--db PATH` before the command. Exact-text deduplication is not duplicate-invoice detection across different text or files.

Review labels are not authenticated identities. The SQLite audit trail is local and not tamper-proof. `APPROVED` records a human review decision only: there are no payment, accounting, banking, or trading integrations.

## Supported checks and boundaries

- Eight required fields: vendor, invoice ID, issue date, due date, currency, subtotal, tax, total.
- A field must cite a complete source line and exactly match the value after a supported label. Conflicting field lines block validation.
- ISO dates only, valid calendar dates, and due date on or after issue date. Explicit DKK, EUR, or USD only.
- Decimal arithmetic requires total = subtotal + tax to the cent. Recognized decimal/grouping formats are tested; ambiguous `1,000` and `1.000` are refused. Negative amounts and credit notes are unsupported.
- Optional source correction only copies a unique value from the exact cited field line. It cannot invent missing evidence, resolve source conflicts, or rescue a truncated generation. Original model output and corrections remain visible.
- Input is UTF-8 text, 1–12,000 characters. No OCR, PDF parsing, line-item reconciliation, vendor verification, exchange rates, purchase-order matching, discounts, or payment authenticity checks.

Real invoices remain in the local database and are sent to the selected local model process. Protect both on a trusted machine. `runtime/`, databases, model weights, and `private-inputs/` are ignored by Git; this is not a substitute for checking files before publishing. All bundled invoice content is fictional.

## Reproduce and inspect

```powershell
python -m unittest discover -s tests -v
invoice-review evaluate --out reports/custom
invoice-review render --input reports/custom/evaluation.json --out reports/custom/report.html
python -m http.server 8775 --bind 127.0.0.1 --directory reports/evaluation
```

Open `http://127.0.0.1:8775/report.html` for the saved report. `evaluate` makes 16 real model calls; unit tests need no model. The protocol saves prompt and fixture hashes, seed, token limit, raw outputs, and timings. Reruns can differ across runtimes/hardware. Exit codes: extraction/import returns 2 for review-needed, 1 for input/runtime errors, and 0 for passed checks; evaluation returns 1 for request errors, not for low accuracy.

Source map: `core.py` extraction/validation/correction; `model.py` local model adapter; `ledger.py` review state; `evaluate.py` metrics/report; `cli.py` commands; `data/cases.json` fictional fixtures. See [VALIDATION.md](VALIDATION.md) and [ATTRIBUTION.md](ATTRIBUTION.md).
