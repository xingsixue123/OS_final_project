#!/bin/bash
# Mirror of baleen_code/data/get-tectonic.sh, but downloading into work/data.
#   bash setup/02_data.sh            # 0.1% sample 0 of all 7 traces + authors' results (~90 MB)
#   bash setup/02_data.sh --samples10  # also 0.1% samples 0-9 (for multi-sample Fig 9 runs)
set -euo pipefail
source "$(dirname "$0")/../env.sh"
URL=https://ftp.pdl.cmu.edu/pub/datasets/Baleen24
D="$REPRO_WORK/data"; mkdir -p "$D"; cd "$D"
get() { [ -f "$1" ] || wget -q --show-progress "$URL/$1"; }

get storage_0.1.tar.gz
if [ ! -d tectonic ]; then tar xf storage_0.1.tar.gz && mv storage tectonic; fi
get results_release.csv.gz
get breakdowns.tar.gz
[ -d breakdown-stats ] || tar xf breakdowns.tar.gz

if [ "${1:-}" = "--samples10" ]; then
    get storage_0.1_10.tar.gz
    if [ ! -f .samples10_done ]; then
        rm -rf _s10 && mkdir _s10 && tar xf storage_0.1_10.tar.gz -C _s10
        cp -rn _s10/storage/. tectonic/ && rm -rf _s10 && touch .samples10_done
    fi
fi

# Verify trace files against the checksums shipped with each trace directory.
# (paths inside checksums.sha1 are relative to tectonic/)
for f in tectonic/*/*/checksums.sha1; do
    (cd tectonic && sha1sum --quiet -c --ignore-missing "${f#tectonic/}") || { echo "CHECKSUM FAIL: $f"; exit 1; }
done
echo "data OK: $(ls tectonic/*/*/full_*_0.1.trace | wc -l) trace files"
