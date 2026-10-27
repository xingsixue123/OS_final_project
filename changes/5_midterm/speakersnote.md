# Speaker script: slides 6–7

括号里是手指的位置，引号里是要念的英文。

## Slide 6 · Results so far

**（开场，还没指表，先讲部件）**

> "Before the table, recall the algorithm slide. PeakBaleen changes Baleen in three places; we call them components.
> One: **new labels**, computed offline by our min–max QUBO with the Ising solver.
> Two: a **load feature**: the model also sees how busy the disks were in the last ten minutes.
> Three: the **adaptive bar**. The model scores each request and admits it if the score is above a bar. Baleen's bar is fixed. Ours drops when the disks are busy and rises when they are quiet, under the same total write budget.
> The table compares us with Baleen from three angles. Every number is the peak, the busiest ten minutes of disk utilization; lower is better."

**（指第 1 行）角度一：离线，只看部件一**

> "Angle one: offline, component one only. We compare the labels themselves, before any model is trained. Our labels give a 13.7 percent lower peak, on 37 of 39 samples. **Offline, we are better.**"

**（指第 2 行）角度二：在线，三个部件全装**

> "Angle two: online, all three components, the full PeakBaleen. Online means we replay the test days in Baleen's simulator, and the model decides request by request without seeing the future. **Here we are worse**: 3.2 percent above Baleen. We win on five of six samples, but one sample collapses."

**（指第 3–6 行，停在有底色的 Region5 那一行）角度三：在线，Baleen 只加部件三**

> "Angle three: online, Baleen plus component three only, the adaptive bar. **Mostly better.** The row that counts is Region5: a cluster we had never run, with the test written down before we ran it. The peak is 3.2 percent lower, and it passes. Region6 plus 7 and Region4 are lower too, but we found those after the fact. On Region1, the lowest-load cluster, there is no gain."

**（指左框）角度二为什么失败**

> "Why did angle two fail? Component one's labels come from day one, and day one's peak was not a scan. So the model learned not to cache big scans. On the sample that collapsed, the test day's peak was a big scan, 48 percent of the peak window. Our model cached 4 to 14 percent of it; Baleen cached more than half. Our labels fit one day's kind of peak."

**（指右框）角度一的收益是不是来自 Ising**

> "Is the offline win from the Ising solver? No. LP and CP-SAT solve the same problem almost as well: 13.0 and 13.2 percent, against 13.7. The win comes from targeting the peak."

**（收尾，接第 7 页）**

> "So: offline, better; the full design online, worse; the adaptive bar alone, mostly better. Our next steps follow from that."

## Slide 7 · Next steps

**（指左上框）补齐基线**

> "One: finish the baselines. Our baseline table covers five of the seven Regions; the proposal promised all seven."

**（指右上框）修角度二**

> "Two: make the oracle's labels transfer. This is the failure in angle two: we need labels that survive a change in the kind of peak, for example by training on several days instead of one."

**（指左下框）拆开看部件**

> "Three: ablations. Angle three shows the components behave differently, so we will measure what each component adds, and when load-awareness helps, by load level and by kind of peak."

**（指右下框）最终测试**

> "Four: the final test. Samples 0.7 to 0.9 of each Region have not been used by any deployed run. We will run them once, for the final claims, and write the paper. Thank you."

## 数字出处

| 数字 | 出处 |
|---|---|
| −13.7%，37/39 | `changes/2_deployable_peak/wp1_offline/RESULTS.md` L9 |
| +3.2%，5/6，崩溃样本 Region7 s0.5 | `changes/5_midterm/result/recompute_out.txt` L20；`changes/2_deployable_peak/wp3_test/RESULTS_test.md` L10, L26 |
| −2.5% / −3.2% / −15.5% / +2.0% | `changes/5_midterm/result/recompute_out.txt` L21–L24 |
| Region5 通过，5/6 | `changes/2_deployable_peak/wp9_region5/RESULTS_test.md` L11 |
| 48%，56–69%，4–14% | `changes/2_deployable_peak/wp3_test/RESULTS_test.md` L45–L47 |
| LP −13.0%，CP-SAT −13.2% | `changes/2_deployable_peak/wp1_offline/RESULTS.md` L7–L8 |
| 0.7–0.9 未被部署实验使用 | `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md` L3 |
