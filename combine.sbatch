#!/bin/bash
#SBATCH --job-name=sir-combine
#SBATCH --partition=general
#SBATCH --mem=1g
#SBATCH --time=00:05:00
#SBATCH --output=logs/combine_%j.out

module load python
python combine.py
