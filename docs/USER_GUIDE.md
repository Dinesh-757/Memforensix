# User Guide

## 1. Sign in
Register an account (role `viewer` by default; ask an admin to promote you to `analyst` for delete permissions). Log in — the JWT is stored client-side and attached to all API/WebSocket calls automatically.

## 2. Upload a memory dump
Go to **Upload**, choose a `.raw/.dmp/.mem/.vmem/.elf/.core` file, and submit. The dump is hashed (SHA-256), format-detected, and queued for analysis. You're redirected to the live Analysis view.

## 3. Watch live progress
The Analysis view opens a WebSocket connection and shows a progress bar moving through stages: `volatility` (process/network extraction) → `yara` (malware scan) → `ml` (anomaly detection) → `complete`.

## 4. Review results

- **Process Tree** — parent/child process hierarchy; red nodes are flagged suspicious.
- **Network Graph** — force-directed graph of local↔remote connections; red edges/nodes are suspicious.
- **Timeline** — chronological process creation events.
- **Threat Indicators** — YARA rule matches (with severity) and ML anomaly findings with plain-language explanations.

## 5. Export a report
From the Analysis view, choose **Export → JSON / CSV / PDF**. The PDF report includes an executive summary table, suspicious-process listing, and YARA match table — suitable for attaching to an incident report or academic submission.

## 6. Managing analyses
The **Dashboard** lists all your past analyses with status chips (queued/running/completed/failed). Analysts and admins can delete analyses.

## Roles

| Role | Permissions |
|---|---|
| `viewer` | Upload, view own analyses/results, export |
| `analyst` | + delete analyses |
| `admin` | + (extend as needed for user management) |
