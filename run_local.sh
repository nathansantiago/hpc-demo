#!/bin/bash
# No cluster? Pretend to be Slurm: run the 20 array tasks in a loop, then combine.
mkdir -p logs results
for i in $(seq 0 19); do
  SLURM_ARRAY_TASK_ID=$i python3 sir.py
done
python3 combine.py
