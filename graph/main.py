import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Parse the benchmark data
data = {
    "Connections": [100, 100, 500, 500, 1000, 1000, 2000, 2000, 5000, 5000, 10000, 10000],
    "Backend": ["Python (uvloop + hiredis)", "Rust", "Python (uvloop + hiredis)", "Rust", "Python (uvloop + hiredis)", "Rust", 
               "Python (uvloop + hiredis)", "Rust", "Python (uvloop + hiredis)", "Rust", "Python (uvloop + hiredis)", "Rust"],
    "Requests_per_sec": [839, 856, 872, 995, 912, 1006, 942, 1032, 1043, 1113, 1279, 1334],
    "p50_latency_sec": [0.09041, 0.07570, 0.46230, 0.41340, 0.97870, 0.08520, 2.03, 1.87, 3.21, 2.88, 4.12, 3.95]
}
df = pd.DataFrame(data)

# 2. Configure clean, professional styling overrides
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 11
})

# 3. Initialize a 1x2 subplot layout
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
colors = {"Python (uvloop + hiredis)": "#377eb8", "Rust": "#ff7f00"}

# Left Panel: Throughput Scaling (RPS)
sns.lineplot(
    data=df, x="Connections", y="Requests_per_sec", hue="Backend", 
    marker="o", linewidth=2.5, palette=colors, ax=axes[0]
)
axes[0].set_title("Throughput Scaling\n(Higher is Better)", pad=10)
axes[0].set_xlabel("Concurrent Connections")
axes[0].set_ylabel("Requests / Second")
axes[0].set_xscale("log")
axes[0].set_xticks([100, 500, 1000, 2000, 5000, 10000])
axes[0].get_xaxis().set_major_formatter(plt.ScalarFormatter())

# Right Panel: Latency Scaling (p50)
sns.lineplot(
    data=df, x="Connections", y="p50_latency_sec", hue="Backend", 
    marker="o", linewidth=2.5, palette=colors, ax=axes[1]
)
axes[1].set_title("Median Latency (p50)\n(Lower is Better)", pad=10)
axes[1].set_xlabel("Concurrent Connections")
axes[1].set_ylabel("Latency (Seconds)")
axes[1].set_xscale("log")
axes[1].set_xticks([100, 500, 1000, 2000, 5000, 10000])
axes[1].get_xaxis().set_major_formatter(plt.ScalarFormatter())

# 4. Render and save the file cleanly
plt.tight_layout()
plt.savefig("result.png", dpi=300)
