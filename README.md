# HPC Clusters: Running Code at Scale

A small, runnable demo from the *HPC Clusters* talk (Team A). It shows how a Slurm **job array** fans one program out into 20 independent runs, and how a **dependent job** gathers the results into a single answer.

**The question:** how does an outbreak's peak change as a disease gets more contagious?

An SIR model splits people into Susceptible → Infected → Recovered. β is how fast infection spreads and γ is how fast people recover. We hold γ fixed and sweep β across 20 values, one per array task. R0 = β / γ.

```
sweep.sbatch ──► sir.py ×20 ──► results/run_00..19.csv ──► combine.py ──► summary.csv (+ peak_vs_R0.png)
 (job array)    (one β each)     (one file per task)        (runs only after all 20 succeed)
```

## What's in the repo

| File | Role |
| --- | --- |
| `sir.py` | One SIR simulation. The Slurm array index (`SLURM_ARRAY_TASK_ID`) picks which β to use and names the output file. Standard library only. |
| `sweep.sbatch` | Slurm job script: a 20-task array (`--array=0-19`), 1 CPU, 1 GB, 5 minutes each. |
| `combine.sbatch` | Slurm job script for the single fan-in job that runs `combine.py`. |
| `combine.py` | Gathers every `results/run_XX.csv` into `summary.csv` and, if matplotlib is installed, draws `peak_vs_R0.png`. |
| `submit.sh` | Cluster launcher: submits the sweep, then submits the combine job with `--dependency=afterok` so it waits for all 20 tasks to succeed. |
| `run_local.sh` | No cluster? Loops over the 20 task indices itself, then runs `combine.py`. |

## Requirements

- Python 3
- Optional: `matplotlib` for the plot (without it you still get `summary.csv`)
- Optional: a [Longleaf](https://help.rc.unc.edu) account (or any Slurm cluster) to run the real thing

## Run it locally (no cluster)

```bash
chmod +x submit.sh run_local.sh
./run_local.sh          # on Windows, use Git Bash or WSL
```

Expected output:

```
task 0 on my-laptop: beta=0.1 peak=10 on day 0
task 1 on my-laptop: beta=0.12 peak=1,482 on day 323
...
task 19 on my-laptop: beta=0.48 peak=46,751 on day 28
combined 20 runs -> summary.csv
saved peak_vs_R0.png
```

`run_local.sh` sets `SLURM_ARRAY_TASK_ID` itself, so `sir.py` can't tell the difference from a real array. It runs the tasks one at a time (about 2 seconds here).

## Run it on a Slurm cluster (Longleaf)

1. **Get access.** Request an account at [help.rc.unc.edu](https://help.rc.unc.edu) → *Request a cluster account* → Longleaf. Connect to the UNC VPN if you're off campus.
2. **Log in** from a terminal:
   ```bash
   ssh <onyen>@longleaf.unc.edu
   ```
   You land on a **login node**. Edit files and submit jobs here, but never run heavy work on it.
3. **Get the code** into your home directory:
   ```bash
   git clone https://github.com/nathansantiago/hpc-demo.git && cd hpc-demo
   # or, from your laptop:
   scp -r . <onyen>@longleaf.unc.edu:~/hpc-demo
   ```
4. **Test one task, then submit all 20:**
   ```bash
   chmod +x submit.sh run_local.sh
   module load python
   python sir.py 7 && rm -rf results   # one-task sanity check, under a second
   ./submit.sh                         # 20 array tasks + the combine job
   squeue --me                         # repeat until your jobs are gone
   ls results | wc -l                  # expect 20
   head -4 summary.csv                 # the answer
   sacct -j <SWEEP_ID> --format=JobID,State,Elapsed,MaxRSS   # right-size next time
   ```

The model has no randomness, so your numbers should match exactly:

```
beta,R0,peak_infected,peak_day,total_infected
0.1,1.0,10,0,356
0.12,1.2,1482,322.6,21160
0.14,1.4,4550,191.7,50937
```

Always launch with `./submit.sh`, not a bare `sbatch`. It creates `logs/` first, and Slurm won't create that folder for you.

**On another cluster?** Change two lines in the `.sbatch` files: the partition (list them with `sinfo`) and the module (find one with `module avail python`).

## Results

Peak infected (out of 100,000 people) rises sharply with R0:

| R0 | Peak infected | Note |
| --- | --- | --- |
| 1.0 | 10 | At the threshold, the outbreak never takes off. |
| 2.0 | ~15,000 | Peak of 15,384 sick at once, on day 91. |
| 4.8 | ~47,000 | About three times higher, and it arrives by day 28. |

Nothing about the simulation had to change to parallelize it. The only cluster-aware line is the one that reads the array index.

## Slurm cheat sheet

| Term | Meaning | In this demo |
| --- | --- | --- |
| Job | One unit of work you submit; gets a job ID | the sweep |
| Partition | A queue of nodes with its own limits | `general` |
| Node | One physical machine in the cluster | wherever Slurm puts us |
| Task / CPU | A process and the cores it may use | 1 task, 1 CPU |
| Array task | One copy of a job with its own index | 20 copies, index 0–19 |
| Wall time | Max run time; Slurm stops the job after it | 5 minutes |

| Command | Does |
| --- | --- |
| `sbatch job.sbatch` | Submit a batch job (prints the job ID) |
| `squeue --me` | List your jobs (`PD` = pending, `R` = running) |
| `scancel <id>` | Cancel a job or array |
| `sacct -j <id>` | History: state, time, memory |
| `sinfo` | Partitions and node states |
| `srun --pty bash` | Interactive shell on a node, to debug before you batch |

Two features turn scripts into pipelines:

- **Job arrays** (`#SBATCH --array=0-19`) launch N copies of one script. Each copy reads its own `SLURM_ARRAY_TASK_ID` and picks its input from it. In `--output`, `%A` is the array job ID and `%a` is the index.
- **Dependencies** (`--dependency=afterok:$SWEEP_ID`) hold job B until every task of job A has succeeded. Also available: `afterany` and `afternotok`.

## Troubleshooting

| You see | Do this |
| --- | --- |
| `invalid partition specified` | Run `sinfo` and use a partition it lists. |
| `module: command not found` | You're on your laptop, not the cluster. `ssh` in first. |
| `module load python` fails | Run `module avail python` and load an exact version it lists. |
| Job sits in `PD` a long time | `squeue --me` shows the reason. `Priority` or `Resources` means wait. Ask for less time and memory to start sooner. |
| No files appear in `logs/` | `logs/` must exist before jobs start. Launch with `./submit.sh`. |
| combine stuck in `PD (DependencyNeverSatisfied)` | A sweep task failed. Read `logs/sir_*.out`, fix it, `scancel` the combine job, and run `./submit.sh` again. |
| `IndentationError` or strange characters | The code was pasted from slides. Copy the files from this repo instead. |
| `matplotlib not found` | Harmless: `summary.csv` is still written. For the plot: `pip install --user matplotlib`. |

To resubmit only failed tasks: `sbatch --array=3,7 sweep.sbatch`, then run `combine.sbatch` yourself.

## Good cluster habits

**Do**
- Test with 1 task before submitting 1,000.
- Request only what you need. Smaller jobs start sooner.
- Check `sacct`, then right-size the next run.
- Use full paths, and put big data on scratch.

**Don't**
- Run heavy work on the login node.
- Flood the queue with thousands of seconds-long jobs. Bundle them into fewer array tasks.
- Guess wall time wildly high "just in case".
- Put passwords or tokens in job scripts.

## Background

**Why clusters.** Your laptop eventually hits one of three walls: a job takes *too long* (one simulation takes 10 hours and you need 500), it's *too big* (more memory or GPUs than one machine has), or there are *too many* runs (a model fit means thousands of independent runs).

**Anatomy of a cluster.** You `ssh` into a **login node**, where you edit files and submit work. **Slurm**, the scheduler, keeps a queue and decides which **compute nodes** run each job and when. A **shared filesystem** gives every node the same files, so the script you write on the login node is the one the compute node reads, and results land back where you can see them.

**Two kinds of workload.**

| | High-performance (HPC) | High-throughput (HTC) |
| --- | --- | --- |
| Shape | One job across many nodes | Many independent jobs |
| Communication | Processes swap messages every step | Jobs never talk to each other |
| Examples | Weather, physics, large-scale ML training | Parameter sweeps, Monte Carlo, model-fitting chains |
| At UNC | Sycamore | Longleaf |

This demo is the high-throughput kind.

**In the wild: flepiMoP.** [flepiMoP](https://github.com/HopkinsIDD/flepiMoP) (Flexible Epidemic Modeling Pipeline, from Johns Hopkins IDD and UNC epidemiology) uses the same pattern at research scale:

| | This demo | flepiMoP |
| --- | --- | --- |
| Unit of work | One β value | One inference slot |
| Inputs | List in `sir.py` | YAML config + data |
| Fan-out | Slurm job array | Slurm batch jobs |
| Fan-in | `combine.py` | Post-processing |
| Model | 3-compartment SIR | Many compartments × places × ages |

## Takeaways

1. A cluster is login node + scheduler + compute nodes + shared storage.
2. A Slurm job is a shell script with a resource request on top.
3. Arrays + dependencies turn one program into a parallel pipeline.

## Where to learn more

- UNC Research Computing: [help.rc.unc.edu](https://help.rc.unc.edu) (accounts, Getting Started on Longleaf, Slurm examples)
- Slurm documentation: [slurm.schedmd.com](https://slurm.schedmd.com) (sbatch options, job arrays, dependencies)
- [UNCIDD/using-longleaf](https://github.com/UNCIDD/using-longleaf): a practical checklist from UNC's infectious disease dynamics group
- [HopkinsIDD/flepiMoP](https://github.com/HopkinsIDD/flepiMoP): source, batch scripts and documentation

