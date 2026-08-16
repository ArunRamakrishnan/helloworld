# Configuration guide

This project separates **secrets/deployment settings** (env vars) from **business
rules** (YAML config), and uses a small set of design patterns so new agents,
brokers, and score tuning don't require editing core pipeline code.

## Precedence

For any given value, in order of priority (highest wins):

1. **Environment variables** (`.env` or real env) — secrets and deployment knobs only:
   API keys, `POSTGRES_URL`, `REDIS_URL`, `PAPER_TRADING`, `LOG_LEVEL`, `APP_ENV`,
   `ACTIVE_BROKER`.
2. **`config/<APP_ENV>.yaml`** — optional per-environment override (`APP_ENV` defaults
   to `development`), deep-merged on top of the file below. e.g. `config/production.yaml`.
3. **`config/default.yaml`** — the base: every scoring threshold/weight, the
   enrichment-agent pipeline order, broker selection default, disclaimer text, and
   category metadata.

Business rules are never read from `.env` — only secrets and deployment knobs are.
See `src/utils/config.py` (pydantic models + `get_config()`/`reload_config()`) and
`src/utils/config_loader.py` (the YAML loader/merger).

## Retuning a score — no code change

Every scoring agent's thresholds and weights live under `scoring.<agent>` in
`config/default.yaml`. For example, to make the ROE bar for a top fundamental score
stricter, edit:

```yaml
scoring:
  fundamental:
    roe_tiers: [[0.35, 10.0], [0.25, 8.0], ...]   # was [[0.30, 10.0], [0.20, 8.0], ...]
```

Tiers are evaluated by `src/utils/scoring.py::tiered_score` — `mode: "gte"` for
higher-is-better ladders (ROE, revenue CAGR), `mode: "lte"` for lower-is-better ones
(PE, debt/equity). Restart the process (or call `reload_config()`) to pick up changes.

Portfolio caps (`scoring.portfolio`), risk red-flag thresholds and descriptions
(`scoring.risk`), moat/fisher/unicorn dimension weights, DCF assumptions
(`scoring.valuation.dcf_defaults`), and the final-rating classification thresholds
(`scoring.synthesis`) all work the same way.

## Adding a new enrichment agent — no orchestrator edit

`Orchestrator` (`src/agents/orchestrator.py`) runs a mandatory sequential chain
(data → fundamental → valuation → risk → synthesis, which have real, non-uniform
data dependencies) plus a config-driven loop of independent **enrichment agents**
(moat, news, sentiment, fisher, unicorn by default) looked up through
`AgentRegistry` (`src/agents/registry.py`) — a Strategy/Factory pattern.

To add one:

1. Write the agent class with an `analyze(ticker, **kwargs) -> dict` method.
2. Give it an `output_key = "your_name"` class attribute (where its result lands in
   the report) and a `pipeline_kwargs(ticker, context) -> dict` staticmethod that
   picks whatever inputs it needs out of the shared context dict (it already contains
   `ticker`, `business_description`, `market_cap_cr`, `articles`, and every flattened
   key from the fundamental/valuation agent outputs — see the existing agents for
   examples, e.g. `src/agents/fisher_agent.py`).
3. Decorate the class: `@AgentRegistry.register("your_name")`.
4. Add `"your_name"` to `pipeline.enabled_agents` in `config/default.yaml`.

Removing a name from `pipeline.enabled_agents` disables that agent's contribution to
`/api/v1/research/{ticker}` — the report builder already reads enrichment fields via
`.get()`, so missing ones are simply omitted.

## Adding a new broker — no BrokerAgent edit

`BrokerAgent._place_live_order` picks a connector via `BrokerFactory`
(`src/brokers/factory.py`) using `config.broker.active_broker` (default `zerodha`,
override with the `ACTIVE_BROKER` env var). Each connector
(`src/brokers/zerodha.py`, `upstox.py`, `angelone.py`, `dhan.py`) subclasses
`BrokerConnector` (`src/brokers/base.py`) and self-registers with
`@BrokerFactory.register("name")`. To add a new broker: write a connector
implementing `place_order`/`cancel_order`, register it, and set `ACTIVE_BROKER` (or
`broker.active_broker` in YAML) to its name.

## Prompts

LLM system prompts live as versioned files in `prompts/system/*.md` (front-matter +
body), loaded via `src/utils/prompts.py::load_prompt(name)` — matching this repo's
existing convention of versioning prompts under `prompts/` (see
`prompts/master_prompt.md`). Edit the `.md` file to change an agent's system prompt;
no Python change needed.

## What's not yet config-driven

Out of scope for this pass, listed here so the pattern is easy to extend later:
`universe_scan.py`, `universe_screener.py`, `unicorn_hunter.py`, and
`quarterly_earnings.py` still have some inline thresholds/taxonomies (e.g.
`TAILWIND_SECTORS`, keyword sentiment word lists). Follow the same
config-model-in-`src/utils/config.py` + `config/default.yaml` pattern used for the
core agents if/when those need to be tunable too.
