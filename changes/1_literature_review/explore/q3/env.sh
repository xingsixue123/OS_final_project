# Source me: confines every runtime write of Track A (q3 + common) to explore/ (X).
Q3="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
X="$(cd "$Q3/.." && pwd)"
export Q3_ROOT="$Q3"
export X_ROOT="$X"
export COMMON="$X/common"
export BALEEN_PY="$X/../../0_reproduce/env/bin/python"      # read-only use
export HOME="$Q3/.home"
export XDG_CACHE_HOME="$Q3/.cache/xdg"
export XDG_CONFIG_HOME="$Q3/.home/.config"
export XDG_DATA_HOME="$Q3/.home/.local/share"
export MPLCONFIGDIR="$Q3/.cache/matplotlib"
export JUPYTER_CONFIG_DIR="$Q3/.home/.jupyter"
export JUPYTER_DATA_DIR="$Q3/.home/.local/share/jupyter"
export JUPYTER_RUNTIME_DIR="$Q3/.cache/jupyter_runtime"
export IPYTHONDIR="$Q3/.home/.ipython"
export PIP_CACHE_DIR="$Q3/.cache/pip"
export CONDA_PKGS_DIRS="$Q3/.cache/conda_pkgs"
export CONDA_REGISTER_ENVS=false
export TMPDIR="$Q3/.cache/tmp"
export TORCH_HOME="$Q3/.cache/torch"
export NUMBA_CACHE_DIR="$Q3/.cache/numba"
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export OMP_WAIT_POLICY=PASSIVE
mkdir -p "$HOME" "$XDG_CACHE_HOME" "$XDG_CONFIG_HOME" "$XDG_DATA_HOME" "$MPLCONFIGDIR" \
         "$JUPYTER_RUNTIME_DIR" "$PIP_CACHE_DIR" "$CONDA_PKGS_DIRS" "$TMPDIR" "$TORCH_HOME" "$NUMBA_CACHE_DIR"
