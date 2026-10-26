# sir.py - one SIR epidemic run; the Slurm array index picks which beta to use
import csv, os, platform, sys

BETAS = [round(0.10 + 0.02 * i, 2) for i in range(20)]  # 20 transmission rates
GAMMA = 0.10                                            # recovery rate
N, I0, DAYS, DT = 100_000, 10, 365, 0.1

def simulate(beta):
    s, i, r = N - I0, I0, 0
    peak, peak_day = i, 0
    for step in range(int(DAYS / DT)):
        new_inf = beta * s * i / N * DT
        new_rec = GAMMA * i * DT
        s, i, r = s - new_inf, i + new_inf - new_rec, r + new_rec
        if i > peak:
            peak, peak_day = i, step * DT
    return peak, peak_day, r

idx = int(os.environ.get("SLURM_ARRAY_TASK_ID", sys.argv[1] if len(sys.argv) > 1 else 0))
beta = BETAS[idx]
peak, peak_day, total = simulate(beta)
os.makedirs("results", exist_ok=True)
with open(f"results/run_{idx:02d}.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["beta", "R0", "peak_infected", "peak_day", "total_infected"])
    w.writerow([beta, round(beta / GAMMA, 1), round(peak), round(peak_day, 1), round(total)])
print(f"task {idx} on {platform.node()}: beta={beta} peak={peak:,.0f} on day {peak_day:.0f}")
