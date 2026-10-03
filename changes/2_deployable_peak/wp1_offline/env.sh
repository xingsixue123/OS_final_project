# Phase-2 Track B sandbox (WP5 Ising track + WP1 offline breadth): source me.
# Confines every runtime write to P2/wp1_offline (WP1 copy of wp5_ising/env.sh).
P2=/home/sxing/project/OS_final_project/changes/2_deployable_peak
A=$P2/wp1_offline
export P2 A
export HOME=$A/.home
export XDG_CACHE_HOME=$A/.cache/xdg XDG_CONFIG_HOME=$A/.home/.config XDG_DATA_HOME=$A/.home/.local/share XDG_STATE_HOME=$A/.home/.local/state
export PIP_CACHE_DIR=$A/.cache/pip CONDA_PKGS_DIRS=$A/.cache/conda_pkgs CONDA_REGISTER_ENVS=false
export TMPDIR=$A/.cache/tmp MPLCONFIGDIR=$A/.cache/mpl TORCH_HOME=$A/.cache/torch NUMBA_CACHE_DIR=$A/.cache/numba
export JUPYTER_CONFIG_DIR=$A/.home/.jupyter JUPYTER_DATA_DIR=$A/.home/.local/share/jupyter IPYTHONDIR=$A/.home/.ipython
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 OMP_WAIT_POLICY=PASSIVE
export SOLVER_PY=/home/sxing/project/OS_final_project/changes/1_literature_review/explore/env/bin/python
export BALEEN_PY=/home/sxing/project/OS_final_project/changes/0_reproduce/env/bin/python
mkdir -p $HOME $XDG_CACHE_HOME $XDG_CONFIG_HOME $XDG_DATA_HOME $XDG_STATE_HOME $PIP_CACHE_DIR $CONDA_PKGS_DIRS $TMPDIR $MPLCONFIGDIR $TORCH_HOME $NUMBA_CACHE_DIR
