#!/bin/bash
#SBATCH --job-name=sir-sweep
#SBATCH --partition=general
#SBATCH --array=0-19
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1g
#SBATCH --time=00:05:00
#SBATCH --output=logs/sir_%A_%a.out

module load python
python sir.py
