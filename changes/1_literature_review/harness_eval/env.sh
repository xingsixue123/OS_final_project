# Source me: confines every runtime write to harness_eval/ (H).
H="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export HE_ROOT="$H"
export HE_WORK="$H/work"
export BALEEN_PY="$H/../../0_reproduce/env/bin/python"      # read-only use
export SOLVER_PY="$H/../ising_followup/audit/env/bin/python" # read-only use
export HOME="$H/.home"
export XDG_CACHE_HOME="$H/.cache/xdg"
export XDG_CONFIG_HOME="$H/.home/.config"
export XDG_DATA_HOME="$H/.home/.local/share"
export MPLCONFIGDIR="$H/.cache/matplotlib"
export JUPYTER_CONFIG_DIR="$H/.home/.jupyter"
export JUPYTER_DATA_DIR="$H/.home/.local/share/jupyter"
export JUPYTER_RUNTIME_DIR="$H/.cache/jupyter_runtime"
export IPYTHONDIR="$H/.home/.ipython"
export PIP_CACHE_DIR="$H/.cache/pip"
export CONDA_PKGS_DIRS="$H/.cache/conda_pkgs"
export CONDA_REGISTER_ENVS=false
export TMPDIR="$H/.cache/tmp"
export TORCH_HOME="$H/.cache/torch"
export NUMBA_CACHE_DIR="$H/.cache/numba"
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$HOME" "$XDG_CACHE_HOME" "$XDG_CONFIG_HOME" "$XDG_DATA_HOME" "$MPLCONFIGDIR" \
         "$JUPYTER_RUNTIME_DIR" "$PIP_CACHE_DIR" "$CONDA_PKGS_DIRS" "$TMPDIR" "$TORCH_HOME" "$NUMBA_CACHE_DIR"
