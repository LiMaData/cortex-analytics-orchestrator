This project is a multi-agent analytics orchestrator (conversational + dashboard modes).
Keep guidance compact and actionable. Prefer small, safe code changes and cite files you edit.

Key pointers for AI coding agents working on this repo
- Big picture: orchestrators manage agents. See `orchestrators/base.py` and `orchestrators/conversational.py`.
  - `BaseOrchestrator` initializes `SharedConfig` and `SharedContextManager` and registers agents.
  - `ConversationalOrchestrator.process_query` flows: DataAgent -> VisualizationAgent -> InsightAgent. Match that ordering when adding features.

- Agents: specialized, single-responsibility classes in `agents/`.
  - `agents/data_agent.py` wraps a Snowflake Session + `CortexAnalyst` for NL→SQL→data.
  - `agents/visualization_agent.py` returns Plotly figures (not serialized). When adding APIs, convert figs to images or JSON explicitly.
  - `agents/insight_agent.py` and `agents/benchmark_agent.py` call Snowflake CORTEX.COMPLETE via `session.sql(...).collect()`; preserve string escaping used there.

- Shared state and caching: `shared/context_manager.py`.
  - Uses file-based cache under `./shared_data` with TTL and JSON files named `cache_<md5>.json`.
  - When modifying cache behavior, keep compatibility with existing cache file shape: {query, result, timestamp, ttl}.

- Configuration patterns: `config/shared_config.py` and `config/agent_config.yaml`.
  - `SharedConfig` is a singleton; load env vars (`dotenv`) for Snowflake credentials. Don't bypass this singleton — use SharedConfig() to access config.
  - Agent defaults live in `config/agent_config.yaml`. When adding config keys, update both YAML and `SharedConfig._default_agent_config()`.

- Snowflake & Cortex integration
  - Connections are created with `snowflake.snowpark.Session.builder.configs({...}).create()` in `DataAgent`.
  - NL→SQL is delegated to `tools/cortex_analyst.py` wrapper (look at how `DataAgent._load_analyst()` is used).
  - When constructing SQL prompts for CORTEX.COMPLETE, the code uses triple-quoted strings and escapes single quotes by doubling (`replace("'", "''")`). Follow that pattern.

- Testing and local runs
  - Install deps from `requirements.txt` and run `main.py` for an interactive REPL that uses `ConversationalOrchestrator`.
  - Streamlit demo referenced in README can run if present: `streamlit run cortex_orchestrator_app.py` (README details sample Snowflake setup).

- Coding conventions & pitfalls
  - Logging: modules configure logging with `logging.getLogger(__name__)`. Use existing logger patterns.
  - Error handling: agents return structured dicts with 'success', 'error', 'sql', 'results'. Maintain this contract when changing `process()` signatures.
  - Type hints are present but lightweight. Prefer preserving current function signatures and return shapes for compatibility.

- Quick examples to reference when editing
  - Add an agent: follow `agents/visualization_agent.py` structure and register it in `orchestrators/conversational.py` via `register_agent('name', instance)`.
  - Use cache: call `self.context.get_query_result(query)` and `self.context.save_query_result(query, result)` from `BaseOrchestrator`.

- When in doubt
  - Keep changes small and well-tested. Run the REPL (`python main.py`) to exercise `process_query` paths.
  - Preserve compatibility with file-based cache and SharedConfig singleton.

Files worth scanning first: README.md, main.py, orchestrators/*.py, agents/*.py, shared/context_manager.py, config/*

If you edit or add runtime config keys, update `config/agent_config.yaml` and `SharedConfig._default_agent_config()` together.

Ask the repo owner for environment values (Snowflake creds and any SEMANTIC_MODEL_STAGE) before making integration changes that require running against real services.
