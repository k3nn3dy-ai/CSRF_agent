#!/usr/bin/env bash
set -euo pipefail

# Run CSRF v2 with zero manual env management.
# - Creates/uses a local .venv (Python 3.11/3.12/3.13)
# - Installs the project editable
# - Loads .env if present
# - Executes the crew

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
proj_root="$(cd "$script_dir/.." && pwd)"
cd "$proj_root"

choose_python() {
	for bin in python3.11 python3.12 python3.13 python3; do
		if command -v "$bin" >/dev/null 2>&1; then
			"$bin" -V 1>/dev/null 2>/dev/null || continue
			ver="$("$bin" -V | awk '{print $2}')"
			major="$(echo "$ver" | cut -d. -f1)"
			minor="$(echo "$ver" | cut -d. -f2)"
			if [[ "$major" -eq 3 && "$minor" -ge 10 && "$minor" -le 13 ]]; then
				echo "$bin"
				return 0
			fi
		fi
	done
	echo "No suitable Python (3.10–3.13) found. Please install Python 3.11 or 3.12." >&2
	exit 1
}

PY_BIN="$(choose_python)"

if [[ ! -d ".venv" ]]; then
	echo "Creating virtualenv with $PY_BIN ..."
	"$PY_BIN" -m venv .venv
fi
source .venv/bin/activate

python -m pip install -U pip >/dev/null
python -m pip install -e . >/dev/null

# Load .env if present
if [[ -f ".env" ]]; then
	set -a
	# shellcheck disable=SC1091
	source .env
	set +a
fi

export PYTHONPATH="$proj_root/src"
if [[ "${QUIET:-0}" == "1" ]]; then
	echo "Running in QUIET mode; streaming output to logs.txt"
	# Hide Python warnings unless explicitly overridden by user
	if [[ -z "${PYTHONWARNINGS:-}" ]]; then
		export PYTHONWARNINGS=ignore
	fi
	exec python -m csrf_v2.main >> logs.txt 2>&1
else
	exec python -m csrf_v2.main
fi


