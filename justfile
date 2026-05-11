# Run targets — execute from repo root with `just <target>`
default:
    @just --list

# Run the Streamlit demo (primary entry-point)
demo:
    uv run streamlit run src/market_watcher/main.py --server.port $DEMO_PORT_STREAMLIT

# Run the headless CLI variant
cli:
    uv run python -m market_watcher.cli

# Reset state (keeps fixtures, drops runs + sqlite)
reset:
    rm -rf data/runs/* data/state.sqlite outputs/*

# Pretty-print the latest trace
trace:
    uv run python -m market_watcher.tools.trace_viewer $(ls -t data/runs/*.json | head -n 1)

# Smoke tests
test:
    uv run pytest tests/ -v
