# Track B sandbox: source me. Confines every runtime write to explore/ (X); Track B state under X/q2.
X=/home/sxing/project/OS_final_project/changes/1_literature_review/explore
Q2=$X/q2
export X Q2
export HOME=$Q2/.home
export XDG_CACHE_HOME=$Q2/.cache/xdg XDG_CONFIG_HOME=$Q2/.home/.config XDG_DATA_HOME=$Q2/.home/.local/share XDG_STATE_HOME=$Q2/.home/.local/state
export PIP_CACHE_DIR=$Q2/.cache/pip CONDA_PKGS_DIRS=$Q2/.cache/conda_pkgs CONDA_REGISTER_ENVS=false
export TMPDIR=$Q2/.cache/tmp MPLCONFIGDIR=$Q2/.cache/mpl TORCH_HOME=$Q2/.cache/torch NUMBA_CACHE_DIR=$Q2/.cache/numba
export JUPYTER_CONFIG_DIR=$Q2/.home/.jupyter JUPYTER_DATA_DIR=$Q2/.home/.local/share/jupyter IPYTHONDIR=$Q2/.home/.ipython
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 OMP_WAIT_POLICY=PASSIVE
export SOLVER_PY=$X/env/bin/python
export BALEEN_PY=/home/sxing/project/OS_final_project/changes/0_reproduce/env/bin/python
mkdir -p $HOME $XDG_CACHE_HOME $XDG_CONFIG_HOME $XDG_DATA_HOME $XDG_STATE_HOME $PIP_CACHE_DIR $CONDA_PKGS_DIRS $TMPDIR $MPLCONFIGDIR $TORCH_HOME $NUMBA_CACHE_DIR
