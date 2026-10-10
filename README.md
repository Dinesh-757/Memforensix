<div align="center">

<a href="https://github.com/Dinesh-757"><img src="https://raw.githubusercontent.com/Dinesh-757/Dinesh-757/main/assets/operation-memforensix.svg" alt="Memforensix in the electric-blue and violet cybersecurity project series" width="100%" /></a>

<img src="https://img.shields.io/badge/DOMAIN-MEMORY%20ANALYSIS-4f46e5?style=for-the-badge&labelColor=0b1027" alt="DIGITAL FORENSICS" />
<a href="https://github.com/Dinesh-757"><img src="https://img.shields.io/badge/CREATOR-DILLI%20DINESH-111936?style=for-the-badge&labelColor=0b1027" alt="Creator Dilli Dinesh" /></a>

[GitHub profile](https://github.com/Dinesh-757) · [Portfolio](https://dinesh-757.github.io/) · [Project dossiers](https://github.com/Dinesh-757/Dinesh-757/blob/main/PROJECT_SHOWCASE.md)

</div>

# MEMFORENSIX

**Memory forensics workbench — Volatility 3 • YARA • anomaly detection**

MEMFORENSIX is a full-stack forensics tool that ingests memory dump images (RAW, DMP, ELF, Mach-O), extracts process and network artifacts via Volatility 3, scans them against YARA malware-indicator rules, runs unsupervised ML anomaly detection, and presents results in an interactive red/black-themed dashboard with real-time progress over WebSockets.

Built as a final-year project demonstrating full-stack + security engineering: FastAPI, Celery, PostgreSQL, Redis, React/TypeScript, Docker, and CI/CD.

> **Evidence boundary:** The bundled demo input is synthetic and can trigger a documented fallback dataset. It is **not** a substitute for parsing and validating a genuine memory capture. Details are in [Important: about the forensics in this demo](#important-about-the-forensics-in-this-demo).

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   React SPA │◄────►│   FastAPI    │◄────►│  PostgreSQL │
│  (nginx)    │  WS  │   Backend    │      │             │
└─────────────┘      └──────┬───────┘      └─────────────┘
                             │
                             ▼
                      ┌──────────────┐      ┌─────────────┐
                      │    Redis     │◄────►│   Celery    │
                      │ (broker/pub) │      │   Worker    │
                      └──────────────┘      └──────┬──────┘
                                                    │
                                    ┌───────────────┼───────────────┐
                                    ▼               ▼               ▼
                              Volatility3        YARA          scikit-learn
                              (pslist/netscan)   (rules)        (IsolationForest)
```

## Features

- Memory dump upload (RAW / DMP / ELF / Mach-O) with format auto-detection
- Process enumeration & tree visualization (parent/child, D3)
- Network connection extraction & force-directed graph visualization
- YARA-based malware/indicator scanning (C2 beacons, process hollowing, Mimikatz, packers, fileless PowerShell)
- Unsupervised ML anomaly detection (IsolationForest) over process/connection feature sets
- Real-time analysis progress via WebSockets (Redis pub/sub relay)
- JWT auth with role-based access (admin / analyst / viewer)
- Report export: JSON, CSV, PDF (reportlab)
- Dockerized multi-service stack; GitHub Actions CI/CD

## Important: about the "forensics" in this demo

This project wires up **real** Volatility 3 and YARA execution paths. However:

- Real Volatility3 plugin analysis requires an **actual OS memory image** (multi-GB Windows/Linux `.dmp`/`.raw` file) and meaningful runtime (minutes). We can't ship one of those.
- `sample_data/demo_sample.raw` is a **synthetic placeholder** file (not a real memory image). When Volatility can't parse a dump (as with this placeholder), `VolatilityService` falls back to a deterministic synthetic dataset so the rest of the pipeline (YARA scan of the raw bytes, ML anomaly detection, UI, reporting) is still fully exercised end-to-end.
- To see real Volatility3 output, supply a genuine memory image (e.g. captured with `winpmem`, `avml`, or a VM snapshot) — no code changes needed, just upload it.
- The YARA rules and ML model are real, working implementations, not stubs.

## Quick Start

```bash
git clone https://github.com/Dinesh-757/Memforensix.git
cd memforensix
cp .env.example .env
cp backend/.env.example backend/.env
docker-compose up -d --build
```

- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/api/v1/docs

Run database migrations (first boot):
```bash
docker-compose exec backend alembic upgrade head
```

Register a user via `/api/v1/auth/register`, then log in through the UI.

## Repository Structure

```
memforensix/
├── backend/            FastAPI + Celery + Volatility/YARA/ML services
├── frontend/            React + TypeScript + Redux Toolkit + MUI
├── docs/                 API, installation, user & developer guides
├── scripts/             setup.sh / deploy.sh
├── sample_data/          demo dump placeholder
├── docker-compose.yml
├── docker-compose.prod.yml
└── .github/workflows/    CI/CD pipelines
```

## Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [API Documentation](docs/API.md)
- [User Guide](docs/USER_GUIDE.md)
- [Developer Guide](docs/DEVELOPER.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Python 3.11, Celery, PostgreSQL, Redis, SQLAlchemy (async), Alembic |
| Forensics | Volatility 3, yara-python |
| ML | scikit-learn (IsolationForest), pandas, numpy |
| Frontend | React 18, TypeScript, Redux Toolkit, Material-UI, D3.js |
| DevOps | Docker, Docker Compose, GitHub Actions |

## License

MIT — see [LICENSE](LICENSE).

---

<sub>Part of the [Dilli Dinesh cybersecurity project collection](https://github.com/Dinesh-757). All testing must be authorized. Documentation describes scope and known limitations, not an independent security certification.</sub>
