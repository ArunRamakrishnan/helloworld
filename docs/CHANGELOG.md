# Changelog

All notable changes to the Indian Investment Research Wizard Agent are documented here.

Format: `[vX.Y.Z] YYYY-MM-DD — Summary`

---

## [v0.1.0] 2026-06-06 — Initial Project Structure

**Prompt Version:** v1  
**Branch:** claude/friendly-cori-RLfF7  
**Author:** arunr.pes@gmail.com  

### Added
- Full project directory structure
- README with architecture overview, quick start, and safety rules
- `docs/architecture.md` — system design, data flow, agent responsibilities
- `docs/compliance.md` — SEBI/legal compliance rules
- `docs/data_sources.md` — allowed data sources and usage rules
- `prompts/master_prompt.md` — active prompt version pointer
- `prompts/prompt_versions/prompt_v1.md` — full v1 system prompt
- All 9 agent modules (skeleton with docstrings and type annotations)
- FastAPI backend skeleton (`src/api/main.py`, `src/api/routes.py`)
- Broker connectors: Zerodha, Upstox, Angel One, DhanHQ
- Data models and repository layer
- Utility modules: logger, config, validators
- Unit test skeletons for all agents
- `.env.example` with all required keys documented
- `requirements.txt` with pinned dependencies
- `docker-compose.yml` with PostgreSQL + ChromaDB services
- GitHub Actions CI workflow

### Changed
- N/A (initial release)

### Removed
- N/A

### Unit Test Results
- Phase 1 setup — tests scaffolded, execution pending environment setup

---
