#!/bin/bash
# Submit the sweep, then a combine job that waits for ALL 20 tasks to succeed.
mkdir -p logs results
SWEEP_ID=$(sbatch --parsable sweep.sbatch)
echo "sweep job: $SWEEP_ID"
sbatch --dependency=afterok:$SWEEP_ID combine.sbatch
