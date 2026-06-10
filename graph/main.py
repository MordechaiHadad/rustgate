import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Parse complete multi-vector metrics
data = {
    "Connections": [100, 100, 500, 500, 1000, 1000, 2000, 2000, 5000, 5000, 10000, 10000],
    "Backend": [
        "Python (uvloop + hiredis)", "Rust",
        "Python (uvloop + hiredis)", "Rust",
        "Python (uvloop + hiredis)", "Rust",
        "Python (uvloop + hiredis)", "Rust",
        "Python (uvloop + hiredis)", "Rust",
        "Python (uvloop + hiredis)", "Rust"
    ],
    "Requests_per_sec": [839, 856, 872, 995, 912, 1006, 942, 1032, 1043, 1113, 1279, 1334],
    "p50_latency_sec": [0.09041, 0.07570, 0.46230, 0.41340, 0.97870, 0.08520, 2.03, 1.87, 3.21, 2.88, 4.12, 3.95],
    "p99_latency_sec": [0.46057, 0.71700, 1.88, 1.45, 2.67, 0.27220, 3.97, 3.39, 18.06, 20.46, 24.55, 21.74],
    "Success_rate_pct": [100.00, 100.00, 100.00, 100.00, 100.00, 100.00, 100.00, 100.00, 95.96, 98.80, 87.90, 89.75]
}
df = pd.DataFrame(data)

# 2. Configure minimalist grid overrides
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 10
})

# 3. Instantiate 2x2 multi-panel layout
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
colors = {"Python (uvloop + hiredis)": "#377eb8", "Rust": "#ff7f00"}

# Formatter helper to enforce identical scaling physics across columns
def apply_common_styles(ax, title, ylabel):
    ax.set_title(title, pad=10, weight='bold')
    ax.set_xlabel("Concurrent Connections")
    ax.set_ylabel(ylabel)
    ax.set_xscale("log")
    ax.set_xticks([100, 500, 1000, 2000, 5000, 10000])
    ax.get_xaxis().set_major_formatter(plt.ScalarFormatter())

# Panel A: Throughput Scaling (RPS)
sns.lineplot(data=df, x="Connections", y="Requests_per_sec", hue="Backend", marker="o", linewidth=2.2, palette=colors, ax=axes[0, 0])
apply_common_styles(axes[0, 0], "Throughput Scaling\n(Higher is Better)", "Requests / Second")

# Panel B: Success Rate Stability Profile
sns.lineplot(data=df, x="Connections", y="Success_rate_pct", hue="Backend", marker="o", linewidth=2.2, palette=colors, ax=axes[0, 1])
apply_common_styles(axes[0, 1], "Success Rate (%)\n(Higher is Better)", "Success Rate (%)")
axes[0, 1].set_ylim(85, 102)  # Zooms into the tail degradation area

# Panel C: Median Latency (p50)
sns.lineplot(data=df, x="Connections", y="p50_latency_sec", hue="Backend", marker="o", linewidth=2.2, palette=colors, ax=axes[1, 0])
apply_common_styles(axes[1, 0], "Median Latency (p50)\n(Lower is Better)", "Latency (Seconds)")

# Panel D: Tail Latency Worst-Case Outliers (p99)
sns.lineplot(data=df, x="Connections", y="p99_latency_sec", hue="Backend", marker="o", linewidth=2.2, palette=colors, ax=axes[1, 1])
apply_common_styles(axes[1, 1], "Tail Latency (p99)\n(Lower is Better)", "Latency (Seconds)")

# 4. Clean boundaries and commit render
plt.tight_layout()
plt.savefig("result.png", dpi=300)
