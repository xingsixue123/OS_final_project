# Source me: confines every runtime write of Track A WP3 preparation (wp3_test) to 2_deployable_peak/.
A="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
P2="$(cd "$A/.." && pwd)"
export WP3_ROOT="$A"
export P2_ROOT="$P2"
export BALEEN_PY="$P2/../0_reproduce/env/bin/python"                    # read-only use
export SOLVER_PY="$P2/../1_literature_review/explore/env/bin/python"    # read-only use
export HOME="$A/.home"
export XDG_CACHE_HOME="$A/.cache/xdg"
export XDG_CONFIG_HOME="$A/.home/.config"
export XDG_DATA_HOME="$A/.home/.local/share"
export MPLCONFIGDIR="$A/.cache/matplotlib"
export JUPYTER_CONFIG_DIR="$A/.home/.jupyter"
export JUPYTER_DATA_DIR="$A/.home/.local/share/jupyter"
export JUPYTER_RUNTIME_DIR="$A/.cache/jupyter_runtime"
export IPYTHONDIR="$A/.home/.ipython"
export PIP_CACHE_DIR="$A/.cache/pip"
export CONDA_PKGS_DIRS="$A/.cache/conda_pkgs"
export CONDA_REGISTER_ENVS=false
export TMPDIR="$A/.cache/tmp"
export TORCH_HOME="$A/.cache/torch"
export NUMBA_CACHE_DIR="$A/.cache/numba"
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export OMP_WAIT_POLICY=PASSIVE
mkdir -p "$HOME" "$XDG_CACHE_HOME" "$XDG_CONFIG_HOME" "$XDG_DATA_HOME" "$MPLCONFIGDIR" \
         "$JUPYTER_RUNTIME_DIR" "$PIP_CACHE_DIR" "$CONDA_PKGS_DIRS" "$TMPDIR" "$TORCH_HOME" "$NUMBA_CACHE_DIR"
