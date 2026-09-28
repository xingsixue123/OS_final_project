# Oracle distillation for cache admission: can peak-aware offline labels be learned by a model with no time/load features?

Scope: learning-from-oracle (imitation of offline-optimal labels) for cache admission/eviction, with a focus on whether time- or load-dependent offline decisions survive distillation into online models that cannot see time or load. The target is PeakBaleen's H3: keep Baleen's LightGBM model and features as they are, and change only the OPT labels so that episode selection minimises the peak 10-min backend DT.

Source handling: all Baleen quotes come from the local copy of the FAST'24 PDF (`documents/Baleen_FAST24_Wong.pdf`, text extracted with pdftotext). LRB, Parrot, Hawkeye, Glider, HALP, CacheSack, Flashield, CACHEUS, RL-Cache, Zhou & Maas and ADVISOR were read from their full-text PDFs. Raven was seen only through its abstract and search listings. Anything marked **[unverified]** was not confirmed in a primary full text.

---

## Q1. How are oracle-imitation caching policies built, and how much of the oracle's gain do they keep online?

### Takeaway
Every system here uses the same recipe: run an offline oracle (Belady/MIN, a relaxed Belady, OPTgen, or an episode-based OPT) on past trace data, turn its decisions into binary or ranking labels, and fit a cheap model on per-object history features. Online, these systems keep only part of the oracle's advantage. LRB closes about a quarter of the gap between the best heuristic and Belady. Baleen leaves 16% of peak DT on the table relative to its own OPT. Parrot reaches the oracle on some SPEC programs and falls well short on others. Where authors explain the remaining gap, they point to prediction error on items that sit at the decision boundary and that the features cannot tell apart.

### Cited Findings

**Baleen (Wong et al., FAST 2024)**
- The oracle is OPT, "an episode-based approximation of optimal admission". It scores each episode by DT saved and admits the highest-scoring episodes until writes reach the write-rate budget. "Baleen learns to imitate OPT, and the binary labels are determined by whether that episode, based on its score, would have been admitted under OPT." — [Baleen, FAST'24 §3.5, §4.1](https://www.usenix.org/conference/fast24/presentation/wong) ([PDF](https://www.usenix.org/system/files/fast24-wong.pdf))
- Training data uses "only the first 6 accesses from each episode … To avoid a training bias towards popular but easy-to-differentiate episodes". The stated goal is "to differentiate episodes at the decision boundary, which tend to have few accesses." — [Baleen §4.1](https://www.usenix.org/system/files/fast24-wong.pdf)
- There are 9 features. The metadata features are namespace (<100 values), user (<200 values), a temp/permanent flag, and size-related fields. The online dynamic features are access counts over the last 1..6 hours at block and segment level, kept in production as count-min sketches that each cover about 1 hour, with a queue of 6. — [Baleen §4.1](https://www.usenix.org/system/files/fast24-wong.pdf)
- Baleen runs a fixed-point loop: it assumes an eviction age (EA, starting at 2 h), generates episodes, trains, simulates online, and re-generates episodes until the assumed EA matches the simulated EA. An inner loop tunes the admission threshold until the target flash write rate is met. — [Baleen §4.1](https://www.usenix.org/system/files/fast24-wong.pdf)
- Baleen designs its admission and prefetching for average DT, not peak. The authors write: "As explicitly optimizing admission for the peak introduces significant complexity, we leave that for future work … we design our admission and prefetching policies to minimize average DT (and show that they are successful in reducing Peak DT)". — [Baleen §3.1](https://www.usenix.org/system/files/fast24-wong.pdf)
- The remaining gap to OPT is 16% ("Fig 13 shows a remaining gap of 16%, indicating significant room for improvement"). Episode analysis attributes 9% of DT to late admissions, meaning episodes admitted after their first access. — [Baleen §5.6](https://www.usenix.org/system/files/fast24-wong.pdf)
- Supplementary Table 3 (10% trace, mean DT) compares models with OPT. GBM has 93.8% offline and 91.1% online accuracy, precision 76.8%, recall 51.9%, F1 0.619, and IO hit rate 49.4% against OPT's 52.7%. A Transformer using 16 past accesses reaches F1 0.576, and an MLP reaches F1 0.502. GBM beat the Transformer by 0.2% "despite only having features for the current access". — [Baleen Supp C, Table 3](https://www.usenix.org/system/files/fast24-wong.pdf)
- Regression targets such as "no. of expected hits" did worse end to end than a binary classifier plus a threshold, "perhaps because their loss functions incentivize performance at all thresholds and not just those at the boundary." — [Baleen §4.1](https://www.usenix.org/system/files/fast24-wong.pdf)

**LRB (Song et al., NSDI 2020)**
- The oracle is a relaxed Belady. Any object whose next request falls beyond the "Belady boundary" (the minimum time-to-next-request among objects that MIN evicts) is a valid eviction. Relaxed Belady itself costs 9–13% more misses than MIN on Wikipedia. — [LRB §3.1–3.2](https://www.usenix.org/system/files/nsdi20-paper-song.pdf)
- Features: 32 deltas (inter-request times), 10 exponentially decayed counters (EDCs), and static features (size, content type). They are kept for objects inside a "sliding memory window" that is tuned on a 20% validation prefix. The model is a GBM that regresses time-to-next-request. The paper lists no time-of-day or load feature. — [LRB §4.3](https://www.usenix.org/system/files/nsdi20-paper-song.pdf)
- State-of-the-art heuristics trail Belady by 25–40% in byte miss ratio. "LRB indeed reduces the gap between state-of-the-art algorithms and Belady, e.g., by about a quarter on most traces … LRB is closer to relaxed Belady, e.g., one third to half the distance on most traces. The remaining gap between LRB and relaxed Belady is due to our model's prediction error." — [LRB §6.5](https://www.usenix.org/system/files/nsdi20-paper-song.pdf)
- Its "good decision ratio" is an offline proxy metric that correlates with end-to-end byte miss ratio. The authors use it to explore the design space without running full simulations. — [LRB §3.3](https://www.usenix.org/system/files/nsdi20-paper-song.pdf)

**Parrot (Liu et al., ICML 2020)**
- Parrot imitates Belady as an MDP policy. It is an attention/LSTM model over the past H accesses (PC and address embeddings), trained with DAgger plus a ranking loss. — [Parrot §3–4](https://arxiv.org/abs/2006.16239)
- It reports a "normalized cache hit rate" defined as (r − r_LRU)/(r_opt − r_LRU), which is exactly a gap-closure fraction. Parrot beats Glider by 20% normalized hit rate averaged over SPEC2006, beats LRU by 16% raw hit rate on average, and reaches 61% normalized / 13.5% raw hit-rate gain over LRU on Web Search. In Table 1 some programs sit close to the oracle and others do not (for example 34.4% against an optimal 43.5%, but 38.6% against 38.8%). — [Parrot §5](https://arxiv.org/pdf/2006.16239)
- Unseen items limit generalisation: "In mcf, 21.6% of the test-time memory addresses did not appear in the training data." — [Parrot §5](https://arxiv.org/pdf/2006.16239)

**Hawkeye (Jain & Lin, ISCA 2016) and Glider (Shi et al., MICRO 2019)**
- In Hawkeye, OPTgen reconstructs Belady's decisions on past accesses "with 99% accuracy", and a PC-indexed counter table learns whether a line is cache-friendly or cache-averse. The authors note that "past behavior does not always model future behavior, so Hawkeye's performance does not match OPT's." It reduces the miss rate by 17.0% over LRU on SPEC2006. — [Hawkeye](https://www.cs.utexas.edu/~lin/papers/isca16.pdf)
- Glider uses Belady (via OPTgen) labels. An offline attention-LSTM over PC history reaches 82.6% accuracy against 72.2% for Hawkeye's predictor, and the online Integer SVM "matches the offline model's accuracy". It reduces the miss rate by 8.9% over LRU, against 7.1% for Hawkeye. — [Glider](https://www.cs.utexas.edu/~lin/papers/micro19c.pdf)

**HALP (Song et al., NSDI 2023, YouTube DRAM cache)**
- HALP learns pairwise "which object is re-accessed later" preferences among eviction candidates at the LRU tail. Labels resolve online from future re-accesses, not from an offline Belady run. Features: 32 inter-access times, 10 EDCs, access count, mean inter-access time, time since last access, and a video end-of-chunk score. There is no time-of-day or load feature. — [HALP §3](https://www.usenix.org/system/files/nsdi23-song-zhenyu.pdf)
- HALP explicitly targets the peak: "We focus on the byte miss ratio during the peak hours … we therefore focus on reducing the 95th percentile byte miss ratio." In production it cut P95 byte miss ratio by 9.1% on average (up to 24%), at 1.8% CPU overhead. — [HALP §2, §5](https://www.usenix.org/system/files/nsdi23-song-zhenyu.pdf)

**CacheSack (Yang et al., ATC 2022, Google Colossus flash cache)**
- CacheSack's oracle is a model rather than a trace oracle. It splits traffic into categories (for databases, the combination of table name and similar attributes, hashed into up to 5000 buckets). For each category it estimates the disk reads and flash cost of 4 policies (AdmitOnWrite, AdmitOnMiss, AdmitOnSecondMiss, NeverAdmit), and it assigns policy fractions per category by solving a fractional knapsack. — [CacheSack §5](https://www.usenix.org/system/files/atc22-yang-tzu-wei.pdf)
- "The model is reset every 5 minutes and is trained based on the" recent window. Training windows from 1 minute to 8 hours "span a majority of the observed time variation of workloads" and do "not significantly impact the performance". In production CacheSack improved TCO by 6.5% (the USENIX abstract figure; the TOS version reports 7.7%). — [CacheSack §6.5, §7](https://www.usenix.org/system/files/atc22-yang-tzu-wei.pdf); [TOS version](https://dl.acm.org/doi/10.1145/3582014)

**Flashield (Eisenman et al., NSDI 2019)**
- Flashield has no oracle. The label is "the number of times each of the objects is hit in the subsequent hour". An SVM on (number of past reads, number of past updates) predicts whether future reads exceed n, and training samples are drawn uniformly over each object's accesses. Predicting the exact count was "highly inaccurate", so the authors switched to binary classification. — [Flashield §4](https://www.usenix.org/system/files/nsdi19-eisenman.pdf)

**Other systems**
- RL-Cache (Kirilin et al., IEEE JSAC 2020) is a model-free RL admission policy. It is not imitation-based. Its 8 features are size, temporal recency, smoothed recency, ordinal recency, smoothed ordinal recency, frequency, frequency/size and frequency×size, with no time-of-day feature. — [RL-Cache JSAC](https://gorinsky.networks.imdea.org/pdf/RL-Cache_JSAC_2020.pdf)
- LeCaR/CACHEUS (Rodriguez et al., FAST 2021) use no oracle. They minimise regret over experts (SR-LRU and CR-LFU) with an adaptive learning rate. — [CACHEUS](https://www.usenix.org/system/files/fast21-rodriguez.pdf)
- Raven (Hu et al., CoNEXT 2022) is "Belady-guided". A Mixture Density Network estimates the distribution of each object's next arrival time, and Raven evicts the object with the highest probability of arriving last. **[Features and gap-to-Belady unverified; abstract only.]** — [Raven, CoNEXT'22](https://dl.acm.org/doi/10.1145/3555050.3569134)
- Zhou & Maas (MLSys 2021) predict per-request label distributions (interarrival time, lifetime) from application-level distributed-trace tags. Accuracy improves 11–33% over non-ML baselines, and the cache hit rate over LRU goes "from 17% to 30%". — [Zhou & Maas MLSys'21](https://proceedings.mlsys.org/paper_files/paper/2021/hash/efe0df3ea4a53a04614ad79e7a8a57de-Abstract.html)

### Inferences
- The retained share of oracle gain varies widely and depends on the workload. Roughly: LRB closes about 25% of the heuristic-to-MIN gap and 33–50% of the gap to its own relaxed oracle. For Baleen the retained share is somewhere below "OPT minus 16%" on peak DT. Parrot reports 0–100% per program in normalized terms. A prior of 30–70% retention is a reasonable, not conservative, planning assumption for H3.
- Baleen's peak gains are already a side effect of distilling average-DT OPT, which the authors state explicitly. H3 therefore asks whether a peak-specific increment on top of that survives. The baseline for that question is Baleen's OPT→ML retention, not zero.

### Gaps
- None of these papers reports how much of an offline oracle's gain on a peak or tail metric the distilled model keeps. HALP targets P95 but has no offline peak oracle.
- The per-trace Baleen gap (beyond "16%") would have to come from the reproduced Figure 13 in our own runs.

---

## Q2. What happens when labels depend on information the model cannot see (Bayes-optimal behaviour, class imbalance, covariate shift)?

### Takeaway
Theory and the caching evidence agree. A student that imitates a teacher with privileged information learns the teacher's policy averaged over everything the student cannot observe: π_IL(o) = E[π_teacher(S) | f(S)=o]. Baleen observed exactly this. First-miss examples with identical features carried different OPT labels, so the model predicted the majority label and learned to reject almost everything on first access. Under a threshold set by the write rate, label information orthogonal to the features acts as label noise, so it is marginalised away rather than learned.

### Cited Findings
- Baleen: "We observed Baleen learning to reject almost all items on the first access (a behavior similar to RejectX). Many training examples shared identical features (on the first miss) but had different labels. Baleen thus predicted the most probable label for each feature set (i.e., Bayes Optimal classifier behavior). Since dynamic, history-based features cannot differentiate unseen items, we hypothesize that better metadata features are required to distinguish the few true positives." — [Baleen §5.6](https://www.usenix.org/system/files/fast24-wong.pdf)
- Baleen on class imbalance: "most items will not be admitted (94% in our experiments) … while ML admission policies may achieve a high ML accuracy, this does not always translate into a high cache hit rate. We found typical solutions (oversampling, undersampling, and sample weights) ineffective at countering the extreme imbalance." — [Baleen §2.4](https://www.usenix.org/system/files/fast24-wong.pdf)
- Baleen on lost first hits: "These lost hits are insignificant for popular items, but have an outsized impact on items with only a few potential hits. There is a long but heavy tail of such items; our traces show many admitted items with 5–8 hits." — [Baleen §2.4](https://www.usenix.org/system/files/fast24-wong.pdf)
- Baleen notes that admission policies run only on misses, so training on the full trace is mismatched unless an online simulation first identifies which accesses are misses. — [Baleen §2.4](https://www.usenix.org/system/files/fast24-wong.pdf)
- ADVISOR (Weihs et al., NeurIPS 2021) gives the policy-averaging result. "When the teaching agent makes decisions with access to privileged information that is unavailable to the student, this information is marginalized during imitation learning, resulting in an 'imitation gap'". Proposition 1 states π_IL(o) = E_μ[π_teach(S) | f(S)=o]. The authors conclude that the student "should imitate the teacher's policy only in settings where the teacher's policy can, in principle, be exactly reproduced by the student". — [ADVISOR, arXiv 2007.12173](https://arxiv.org/pdf/2007.12173); [NeurIPS'21 proceedings](https://dl.acm.org/doi/10.5555/3540261.3541724)
- A follow-up, "A Bayesian Solution to the Imitation Gap" (arXiv 2024), addresses the same problem. **[Content not read; cited as existence only.]** — [arXiv 2407.00495](https://arxiv.org/pdf/2407.00495)
- Covariate shift in cache imitation, from Parrot: "training off-policy on roll-outs of Belady's should lead to compounding errors, as the states visited during training under Belady's differ from those visited during test time. Empirically, we observe that this is highly program-dependent … training on-policy leads to an average 9.8% normalized cache hit rate improvement over off-policy training." — [Parrot §5 ablation](https://arxiv.org/pdf/2006.16239)
- Zhou & Maas state that "features do not always capture all details in the system that determine the file's lifetime … there is not a single value that we could predict that is correct most of the time". Their response is to predict distributions rather than points. — [Zhou & Maas §3](https://proceedings.mlsys.org/paper_files/paper/2021/file/efe0df3ea4a53a04614ad79e7a8a57de-Paper.pdf)
- LRB labels examples lazily when the next request arrives, or once it is known to lie beyond the Belady boundary. It samples training data to avoid a popularity bias. Baleen's first-6-accesses rule serves the same purpose. — [LRB §4.2](https://www.usenix.org/system/files/nsdi20-paper-song.pdf)

### Inferences
- **Applying this to H3.** Let x be Baleen's features. Let y_avg be the current OPT label and y_peak the peak-aware label. The model learns p(y_peak=1 | x), and admission is thresholded to hit the write budget. The peak gain survives only through the part of the relabelling that changes the ranking of p(·|x) across feature cells. A relabelling that depends only on "does this episode's hit mass fall in the peak window", independent of x, turns into uniform label noise, and after the threshold is re-tuned for the write rate the ML policy is essentially unchanged.
- **Where x may carry peak signal.** Access counts over 1–6 h are per-object and do not encode global load. But namespace/user can correlate with the jobs that create the peak (for example batch tenants whose traffic lands in the peak interval), and recent-count patterns can correlate with objects that are ramping into a burst. H3 therefore depends on how much peak-window membership is explained by metadata. This can be measured directly (see Q4).
- The late-admission and first-miss problem (9% of DT) probably gets worse for peak labels. If an object is valuable only because of hits inside the peak, it has to be admitted before the peak on accesses that look identical to non-peak objects.
- Imbalance probably gets worse too. If peak-aware OPT spends the same write budget on fewer, more peak-concentrated episodes, the positive rate falls below 6%. Baleen reports that reweighting did not help.

### Gaps
- No caching paper was found that explicitly tests imitation of a time-dependent or load-dependent oracle with time-blind features.
- ADVISOR's evidence comes from gridworld and 3D environments, not caching. Carrying it over to caching is an inference.

---

## Q3. What time-aware or load-aware caching and admission policies exist, and what features do they use?

### Takeaway
Among learned cache policies, peak awareness is almost always put into the objective or the evaluation metric (HALP's P95, Baleen's Peak DT/TCO) and not into the features. The feature sets of LRB, HALP, Baleen, RL-Cache and Flashield contain no time-of-day or global-load input. Systems that really are time-aware get there by scheduling: off-peak fill windows (Netflix), coded-caching placement/delivery phases, or frequent re-optimisation on a recent window (CacheSack every 5 min). None of them use a learned model that reads the clock. Baleen's one direct attempt, admitting only during high load, saved writes but did not reduce Peak DT.

### Cited Findings
- Baleen's direct peak experiment: "DT varying over time, with a peak-to-mean ratio of 2. A policy wanting to optimize Peak DT should be aware of the current load level and able to adapt to it. We performed a simple extension where we only admitted to the cache during periods of high load. We found that while this saved flash writes, it did not reduce Peak DT. This suggests that more fundamental changes (e.g., scoring episodes by their usefulness in reducing Peak DT) will be required to optimize explicitly for peak load." — [Baleen §5.6](https://www.usenix.org/system/files/fast24-wong.pdf)
- Baleen already optimises for the peak at the configuration level. "ML-When is not aggressive enough as it optimizes for the mean, not Peak DT", so Baleen "choose[s] another prefetching option per workload … if it is better at reducing Peak DT in training". Baleen-TCO also picks the flash write rate that minimises TCO through Peak DT. — [Baleen §4.3](https://www.usenix.org/system/files/fast24-wong.pdf)
- HALP optimises the peak-hour P95 byte miss ratio, but all its features are per-object access statistics. — [HALP §2, Table 1](https://www.usenix.org/system/files/nsdi23-song-zhenyu.pdf)
- CacheSack re-solves its per-category knapsack on a window that resets every 5 minutes. Time adaptivity therefore comes from refitting, not from features. — [CacheSack §6.5](https://www.usenix.org/system/files/atc22-yang-tzu-wei.pdf)
- Netflix Open Connect: "we can predict with high accuracy what our members will watch and what time of day they will watch it, we make use of non-peak bandwidth to download the vast majority of content updates to the OCAs … during these configurable time windows." This is proactive placement, not reactive admission. — [Open Connect Overview (Netflix PDF)](https://openconnect.netflix.com/Open-Connect-Overview.pdf); see also [Netflix TechBlog "Netflix and Fill"](http://techblog.netflix.com/2016/08/netflix-and-fill.html) **[blog not fetched]**
- Coded caching (Maddah-Ali & Niesen) has a placement phase during off-peak hours and a coded delivery phase during peak hours, and targets peak-rate reduction. — summarised via [arXiv 2201.10646 background](https://arxiv.org/pdf/2201.10646) **[original IEEE T-IT 2014 paper not fetched]**
- Zhou & Maas check their learned caching gain across "three time intervals spanning the three different parts of a 24-hour cycle … the improvements of the learned strategy over the baseline remain similar". This shows robustness to time of day, not exploitation of it. — [Zhou & Maas, Fig 10](https://proceedings.mlsys.org/paper_files/paper/2021/file/efe0df3ea4a53a04614ad79e7a8a57de-Paper.pdf)
- LRB's deployment motivation reports CDN CPU load at peak (below 30% peak CPU), but the policy has no load input. — [LRB §2](https://www.usenix.org/system/files/nsdi20-paper-song.pdf)

### Inferences
- The literature gives no precedent for a learned admission classifier that recovers peak-specific behaviour without a time or load feature. H3 would be new evidence either way, including a negative result.
- Baleen's failed "admit only at high load" experiment suggests timing is necessary but not sufficient. To reduce peak DT, content that will be hit during the peak must be resident, and that often means admitting before the peak. That is what an episode-scoring (label-side) change addresses, as the Baleen authors themselves suggest.

### Gaps
- No academic paper was found on ML flash-cache admission that uses time-of-day or backend-load features and reports the peak effect. Industrial practice (Netflix) is documented only at the level of an overview.
- DeepCache-style (Narayanan et al., NetAI 2018) popularity forecasting uses time series, but it was not read here. **[unverified]**

---

## Q4. What does this imply for H3, and how can the risk be reduced?

### Takeaway
Treat H3 as a measurement, with the following bound as a prior: the distilled model can capture at most the part of the peak-aware relabelling that is predictable from Baleen's 9 features, and a write-rate-matched threshold will absorb part of even that. Each of the following is cheap and fits the "unchanged model" constraint: a label-purity (Bayes-ceiling) diagnostic, a retention ratio defined like Parrot's normalized hit rate, sample weighting instead of hard relabelling, and a DAgger/EA-style retraining loop. A time-dependent threshold or a single global-load feature are the smallest deviations from that constraint, if they turn out to be needed.

### Cited Findings (basis for the recommendations)
- The student learns E[teacher | observation] (ADVISOR Prop. 1), and Baleen learned the most probable label per feature set. The feature-conditional label distribution therefore bounds what H3 can capture. — [ADVISOR](https://arxiv.org/pdf/2007.12173); [Baleen §5.6](https://www.usenix.org/system/files/fast24-wong.pdf)
- Gap-closure metric: Parrot's normalized hit rate (r − r_base)/(r_opt − r_base). — [Parrot §5](https://arxiv.org/pdf/2006.16239)
- The LRB/Baleen pattern: the remaining gap is attributed to prediction error at the boundary, and relaxed-oracle and good-decision-ratio proxies stand in for expensive simulation. — [LRB §3.3, §6.5](https://www.usenix.org/system/files/nsdi20-paper-song.pdf)
- On-policy relabelling (DAgger) gave +9.8% normalized hit rate on average in Parrot, with large variation across programs. Baleen's EA fixed-point loop is a partial on-policy correction. — [Parrot](https://arxiv.org/pdf/2006.16239); [Baleen §4.1](https://www.usenix.org/system/files/fast24-wong.pdf)
- Periodic re-optimisation instead of time features (CacheSack, 5-minute resets). — [CacheSack](https://www.usenix.org/system/files/atc22-yang-tzu-wei.pdf)
- Oversampling and sample weights did not fix imbalance in Baleen. — [Baleen §2.4](https://www.usenix.org/system/files/fast24-wong.pdf)

### Inferences (proposed protocol and mitigations; these are our proposals, not results from the literature)
1. **Define H3 as a retention ratio.** Use R = (PeakDT_ML-avg − PeakDT_ML-peak) / (PeakDT_OPT-avg − PeakDT_OPT-peak), at a matched flash write rate, on held-out days. This mirrors Parrot's normalized hit rate. Report it next to Baleen's own OPT→ML retention on average DT, so that R is compared against a baseline and not against 1.
2. **Bayes-ceiling diagnostic, computed before training.** Bin training examples by the exact 9-feature vector, or by LightGBM leaf. For each bin, compute the fraction of labels that flip from y_avg to y_peak, and the best achievable "admit-top-k-bins" peak DT. If most flipped labels fall in bins whose p(y=1|x) barely changes, H3 will fail by construction (policy averaging). This is cheap and separates "not learnable from these features" from "the model failed to learn it".
3. **Check the feature–peak correlation.** Measure the mutual information between peak-window membership of an episode's hits and namespace, user, and the 1–6 h count features. The metadata features are Baleen's only plausible carriers of peak signal.
4. **Prefer soft labels or sample weights over hard relabelling.** For example, weight each episode by its DT saved inside the peak window, or train on the peak-marginal score. This changes the ranking across feature cells rather than injecting noise inside a cell. Baleen reports that reweighting alone did not fix imbalance, so pair it with the first-6-access sampling rule, which is already in place.
5. **Re-tune the threshold, and consider a time-varying one.** The write-rate-matching loop will partly undo relabelling. A time-dependent threshold schedule, where the model is unchanged but the cutoff is lower before and during the peak, is the smallest intervention that gives the online policy a time signal. It resembles CacheSack's periodic refit and Netflix's fill windows. It must admit before the peak: Baleen found that admitting only during high load did not help.
6. **On-policy relabelling.** Re-run peak-aware OPT on the cache states induced by the learned policy (DAgger-style, extending Baleen's EA loop). This addresses the covariate shift that Parrot showed can be worth about 10% of gap closure.
7. **Minimal feature extension as an ablation (breaks the "unchanged" constraint).** Add one global feature, such as a 10-min backend-DT EWMA or hour-of-day. If R rises sharply, the limiting factor was observability and not labelling. None of the surveyed learned policies uses such a feature, so this would itself be a contribution.
8. **Expect a mostly-reject regime.** Baleen already learns RejectX-like first-access behaviour. Peak-aware labels probably increase that tendency, so watch recall on the peak window and not global accuracy (Baleen: accuracy does not translate into hit rate).

### Gaps
- There is no empirical prior in the literature for R on a peak-type metric. It has to be measured.
- Whether Baleen's metadata features (namespace/user) correlate with peak-window traffic on the Meta Tectonic traces is unknown and has to be computed from the traces.
