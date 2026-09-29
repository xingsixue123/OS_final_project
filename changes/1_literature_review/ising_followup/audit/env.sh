A=/home/sxing/project/OS_final_project/changes/1_literature_review/ising_followup/audit
export HOME=$A/.home XDG_CACHE_HOME=$A/.cache/xdg XDG_CONFIG_HOME=$A/.home/.config XDG_DATA_HOME=$A/.home/.local/share
export PIP_CACHE_DIR=$A/.cache/pip CONDA_PKGS_DIRS=$A/.cache/conda_pkgs CONDA_REGISTER_ENVS=false
export TMPDIR=$A/.cache/tmp MPLCONFIGDIR=$A/.cache/mpl TORCH_HOME=$A/.cache/torch NUMBA_CACHE_DIR=$A/.cache/numba
export PYTHONNOUSERSITE=1 PATH=$A/env/bin:$PATH
mkdir -p $HOME $XDG_CACHE_HOME $XDG_CONFIG_HOME $XDG_DATA_HOME $PIP_CACHE_DIR $CONDA_PKGS_DIRS $TMPDIR $MPLCONFIGDIR $TORCH_HOME $NUMBA_CACHE_DIR
