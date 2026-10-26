# combine.py - gather every results/run_XX.csv into summary.csv (+ a plot if possible)
import csv, glob

rows = []
for path in sorted(glob.glob("results/run_*.csv")):
    with open(path) as f:
        rows.extend(csv.DictReader(f))
with open("summary.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)
print(f"combined {len(rows)} runs -> summary.csv")

try:
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.plot([float(r["R0"]) for r in rows], [int(r["peak_infected"]) for r in rows], "o-")
    plt.xlabel("R0"); plt.ylabel("Peak infected"); plt.title("SIR sweep: 20 Slurm array tasks")
    plt.savefig("peak_vs_R0.png", dpi=150); print("saved peak_vs_R0.png")
except ImportError:
    print("matplotlib not found - skipping plot (summary.csv is still there)")
