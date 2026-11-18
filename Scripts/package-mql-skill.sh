#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; assert sys.version_info >= (3, 10)' >/dev/null 2>&1; then
    python_command=python3
elif command -v python >/dev/null 2>&1 && python -c 'import sys; assert sys.version_info >= (3, 10)' >/dev/null 2>&1; then
    python_command=python
else
    printf '%s\n' 'Python 3.10 or newer is required to package the MQL skill.' >&2
    exit 1
fi
command -v git >/dev/null 2>&1 || { printf '%s\n' 'Git is required.' >&2; exit 1; }
exec "$python_command" "$script_dir/package_mql_skill.py" "$@"
