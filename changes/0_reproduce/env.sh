# Source me:  source changes/0_reproduce/env.sh
# Confines every runtime write (python, jupyter, matplotlib, pip, conda, tmp)
# to changes/0_reproduce/. The frozen artifact in baleen_code/ is never written.

R0="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export REPRO_ROOT="$R0"
export REPRO_CODE="$R0/baleen_code"          # frozen, read-only
export REPRO_WORK="$R0/work"                 # cwd for every job (data/ runs/ tmp/)
export REPRO_ENV="$R0/env"                   # conda prefix env
export REPRO_PY="$REPRO_ENV/bin/python"

# Sandbox home and caches.
export HOME="$R0/.home"
export XDG_CACHE_HOME="$R0/.cache/xdg"
export XDG_CONFIG_HOME="$R0/.home/.config"
export XDG_DATA_HOME="$R0/.home/.local/share"
export MPLCONFIGDIR="$R0/.cache/matplotlib"
export JUPYTER_CONFIG_DIR="$R0/.home/.jupyter"
export JUPYTER_DATA_DIR="$R0/.home/.local/share/jupyter"
export JUPYTER_RUNTIME_DIR="$R0/.cache/jupyter_runtime"
export IPYTHONDIR="$R0/.home/.ipython"
export PIP_CACHE_DIR="$R0/.cache/pip"
export CONDA_PKGS_DIRS="$R0/.cache/conda_pkgs"
export CONDA_REGISTER_ENVS=false   # do not append this env to ~/.conda/environments.txt
export TMPDIR="$R0/.cache/tmp"
export PYTHONNOUSERSITE=1          # ignore ~/.local site-packages
export PYTHONDONTWRITEBYTECODE=1   # no __pycache__ (matches the artifact's `py -B`)
export PATH="$REPRO_ENV/bin:$PATH"

mkdir -p "$HOME" "$XDG_CACHE_HOME" "$XDG_CONFIG_HOME" "$XDG_DATA_HOME" "$MPLCONFIGDIR" \
         "$JUPYTER_RUNTIME_DIR" "$PIP_CACHE_DIR" "$CONDA_PKGS_DIRS" "$TMPDIR"
