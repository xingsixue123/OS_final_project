# The machine

Every fact below was measured on the target machine on 2026-09-13. Judge "can we build
and run this?" against this sheet, not against a typical lab server.

## Access — the binding constraints

| resource | status | consequence |
|---|---|---|
| root / sudo | **none** (password required, not available) | no kernel changes, no kernel modules, no reboot, no `apt install`, no `/etc` or `/proc/sys` writes, no hugepage setup, no `cpupower`/MSR |
| eBPF | **disabled** for unprivileged users (`unprivileged_bpf_disabled=2`) | no bpftrace, BCC, libbpf programs, sched_ext |
| hardware perf counters | **blocked** (`perf_event_paranoid=3`) | no `perf stat/record`, PAPI, likwid; wall-clock and user-space timers only |
| KVM | **no access** (`/dev/kvm` is root:kvm, user not in group) | no hardware-accelerated VMs; QEMU TCG only (very slow) |
| Docker / Podman | **not installed** | Docker-only artifacts must be ported by reading the Dockerfile and installing the same deps with conda/pip/source |
| user namespaces | available (`bwrap` works) | unprivileged sandboxes / containers-lite are possible |
| cgroup v2 | cgroup2 mounted; `cpu memory pids` controllers delegated to the user slice | some CPU/memory limiting experiments possible without root |
| FUSE | `/dev/fuse` is world-rw, `fusermount3` is setuid | user-space file systems can be mounted |
| other machines | **none** — single machine only | no multi-node experiments; distributed behaviour only via simulation or multiple processes on this host |

## Hardware

| resource | value |
|---|---|
| CPU | AMD Ryzen Threadripper PRO 5955WX (Zen 3), 16 cores / 32 threads, 1 NUMA node; AVX2, FMA, F16C — **no AVX-512, no AVX-VNNI** |
| RAM | 125 GiB (+44 GiB swap); 111 GiB available at measurement time (shared machine) |
| GPU | **1 × NVIDIA RTX A5000, 24 GB**, Ampere, compute capability 8.6 |
| GPU driver | 535.216.01 (supports CUDA ≤ 12.2 natively) |
| storage | 2 × Samsung PM9A3 1.7 TB NVMe (software RAID); **~257 GB free** on /home |
| network | internet access; GitHub, arXiv, Hugging Face (non-gated) reachable |

GPU notes: Ampere means FlashAttention-2 works, but **FP8 kernels do not** (they need
Ada/Hopper). 24 GB fits ~7–8B-parameter models in FP16 for inference (more with
quantization); 70B-class models do not fit. CUDA 12.x user-space wheels usually run on
driver 535 through minor-version compatibility, but features needing a newer driver
(some JIT/PTX paths, CUDA 12.4+ specific kernels) are a risk worth flagging.

## Software

| tool | version |
|---|---|
| OS | Debian 12 (12.15), Linux 6.1 |
| gcc / make / cmake | 12.2.0 / 4.3 / 3.25.1 |
| CUDA toolkit (system `nvcc`) | 11.8 — newer toolkits installable per-user through conda |
| Python | 3.12 (miniconda, conda 24.3); new conda envs with any Python version can be created |
| Java | OpenJDK 21.0.4 and 17.0.1, user-installed under `~/local/java`, already on `PATH` |
| glibc | 2.36 |
| newer cmake | `pip install cmake` provides cmake 4.x in user space (checked 2026-09-14) |
| not installed (installable in user space via conda/rustup) | clang/LLVM, Rust, Go |
| git | 2.39 |

Anything not listed can be installed only **in user space** (conda, pip, building from
source into `$HOME`). Anything that needs a system package with no user-space route is a
blocker.
