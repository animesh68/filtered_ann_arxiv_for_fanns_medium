"""
Experiment 09: Visualization and Publication Figures Generator for Medium Dataset.
Generates 300 DPI publication-quality figures:
1. Recall vs Filter Selectivity across workloads
2. Recall vs Query Latency Trade-off (EMIS workload Pareto curve)
3. Query Throughput (QPS) Comparison Across Workloads
4. Overfetching Multiplier Sensitivity Curve
5. Tail Latency (Mean, Median, P95, P99) Comparison
"""

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Styling configuration
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.titlesize'] = 14

RESULTS_DIR = Path("results/controlled_benchmark")
FIGURES_DIR_REPORTS = Path("reports/figures")
FIGURES_DIR_MEDIUM = Path("figures/medium")
FIGURES_DIR_REPORTS.mkdir(parents=True, exist_ok=True)
FIGURES_DIR_MEDIUM.mkdir(parents=True, exist_ok=True)


def save_figure(fig, filename: str):
    """Saves figure to both reports/figures and figures/medium."""
    p1 = FIGURES_DIR_REPORTS / filename
    p2 = FIGURES_DIR_MEDIUM / filename
    fig.savefig(p1, dpi=300, bbox_inches="tight")
    fig.savefig(p2, dpi=300, bbox_inches="tight")
    print(f"  [OK] Saved: {p1} & {p2}")


def plot_recall_vs_selectivity(df_raw: pd.DataFrame):
    """Plot Recall@10 vs Filter Selectivity across methods."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5), sharey=True)
    filter_types = ["EM", "Range", "EMIS"]

    methods_to_plot = [
        ("ExactSearch", "#2ca02c", "-", "o"),
        ("PreFilter", "#1f77b4", "-", "s"),
        ("HNSW_PostFilter", "#d62728", "--", "x"),
        ("HNSW_Overfetch_5x", "#ff7f0e", "--", "^"),
        ("HNSW_Overfetch_20x", "#9467bd", "-.", "v"),
        ("InGraphFilter", "#8c564b", "-", "d"),
        ("UNIFY_Approx", "#e377c2", "-", "*"),
    ]

    for ax, ftype in zip(axes, filter_types):
        sub_df = df_raw[df_raw["filter_type"] == ftype]
        for method_name, color, ls, marker in methods_to_plot:
            m_sub = sub_df[sub_df["method"] == method_name]
            if len(m_sub) == 0:
                continue

            m_sub = m_sub.copy()
            m_sub["sel_bin"] = pd.qcut(m_sub["selectivity"], q=5, duplicates="drop")
            binned = m_sub.groupby("sel_bin", observed=True).agg(
                sel_mean=("selectivity", "mean"),
                rec_mean=("recall_at_k", "mean"),
            ).sort_values("sel_mean")

            ax.plot(
                binned["sel_mean"],
                binned["rec_mean"],
                label=method_name,
                color=color,
                linestyle=ls,
                marker=marker,
                linewidth=2,
                markersize=7,
            )

        ax.set_title(f"Workload: {ftype}")
        ax.set_xlabel("Filter Selectivity (Matching Ratio)")
        ax.set_ylim(-0.05, 1.05)
        ax.grid(True, alpha=0.3)

    axes[0].set_ylabel("Mean Recall@10")
    axes[0].legend(loc="lower right", framealpha=0.9)
    plt.suptitle("Recall@10 vs Filter Selectivity across Filter Workloads (Medium Dataset: 100K Vectors)", y=1.02)
    plt.tight_layout()
    save_figure(fig, "recall_vs_selectivity.png")
    plt.close()


def plot_recall_vs_latency_tradeoff(df_summary: pd.DataFrame):
    """Plot Recall vs Query Latency Pareto Curve."""
    fig, ax = plt.subplots(figsize=(10, 6))

    emis_df = df_summary[df_summary["filter_type"] == "EMIS"].sort_values("mean_latency_ms")
    colors = plt.cm.tab10(np.linspace(0, 1, len(emis_df)))

    for idx, (_, row) in enumerate(emis_df.iterrows()):
        ax.scatter(row["mean_latency_ms"], row["mean_recall"], color=colors[idx], s=130, zorder=5)
        ax.annotate(
            row["method"],
            (row["mean_latency_ms"], row["mean_recall"]),
            textcoords="offset points",
            xytext=(7, -2),
            fontsize=9,
            weight="bold" if "PreFilter" in row["method"] or "InGraph" in row["method"] else "normal",
        )

    ax.set_xlabel("Mean Query Latency (ms)")
    ax.set_ylabel("Mean Recall@10")
    ax.set_title("Recall@10 vs Query Latency Trade-off (EMIS Workload - Medium Dataset: 100K Vectors)")
    ax.set_ylim(0.0, 1.05)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    save_figure(fig, "recall_vs_latency_tradeoff.png")
    plt.close()


def plot_qps_comparison(df_summary: pd.DataFrame):
    """Plot QPS across methods for EM, Range, and EMIS."""
    fig, ax = plt.subplots(figsize=(12, 6))

    pivot_qps = df_summary.pivot(index="method", columns="filter_type", values="qps")
    pivot_qps.plot(kind="bar", ax=ax, width=0.8, colormap="viridis")

    ax.set_title("Query Throughput (QPS) Comparison Across Filter Workloads (100K Vectors)")
    ax.set_ylabel("Queries Per Second (QPS)")
    ax.set_xlabel("Search Strategy")
    ax.grid(True, axis="y", alpha=0.3)
    plt.xticks(rotation=40, ha="right")
    plt.tight_layout()
    save_figure(fig, "qps_comparison.png")
    plt.close()


def plot_overfetch_sensitivity(df_summary: pd.DataFrame):
    """Plot Overfetching Multiplier vs Recall & Latency."""
    overfetch_csv = Path("results/hnsw_overfetch/hnsw_overfetch_summary.csv")
    if overfetch_csv.exists():
        df_of = pd.read_csv(overfetch_csv)
        workloads = ["EM", "Range", "EMIS"]
        colors = {"EM": "#1f77b4", "Range": "#2ca02c", "EMIS": "#d62728"}
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        for w in workloads:
            w_sub = df_of[df_of["filter_type"] == w].sort_values("param_overfetch_factor")
            factors = w_sub["param_overfetch_factor"].values
            recalls = w_sub["mean_recall"].values
            latencies = w_sub["mean_latency_ms"].values

            ax1.plot(factors, recalls, marker="o", linewidth=2, label=w, color=colors[w])
            ax2.plot(factors, latencies, marker="s", linewidth=2, label=w, color=colors[w])
    else:
        overfetch_methods = [
            ("HNSW_PostFilter", 1.0),
            ("HNSW_Overfetch_2x", 2.0),
            ("HNSW_Overfetch_5x", 5.0),
            ("HNSW_Overfetch_10x", 10.0),
            ("HNSW_Overfetch_20x", 20.0),
        ]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        workloads = ["EM", "Range", "EMIS"]
        colors = {"EM": "#1f77b4", "Range": "#2ca02c", "EMIS": "#d62728"}

        for w in workloads:
            factors = []
            recalls = []
            latencies = []
            for m_name, factor in overfetch_methods:
                row = df_summary[(df_summary["method"] == m_name) & (df_summary["filter_type"] == w)]
                if len(row) > 0:
                    factors.append(factor)
                    recalls.append(row["mean_recall"].values[0])
                    latencies.append(row["mean_latency_ms"].values[0])

            if factors:
                ax1.plot(factors, recalls, marker="o", linewidth=2, label=w, color=colors[w])
                ax2.plot(factors, latencies, marker="s", linewidth=2, label=w, color=colors[w])

    ax1.set_title("Recall@10 vs Overfetch Factor")
    ax1.set_xlabel("Overfetch Factor ($k_{fetch} / k$)")
    ax1.set_ylabel("Mean Recall@10")
    ax1.set_ylim(-0.05, 1.05)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc="lower right")

    ax2.set_title("Query Latency vs Overfetch Factor")
    ax2.set_xlabel("Overfetch Factor ($k_{fetch} / k$)")
    ax2.set_ylabel("Mean Latency (ms)")
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc="upper left")

    plt.suptitle("HNSW Overfetching Multiplier Sensitivity Analysis (100K Vectors: 1x to 50x)", y=1.02)
    plt.tight_layout()
    save_figure(fig, "overfetch_sensitivity.png")
    plt.close()


def generate_all_plots():
    raw_path = RESULTS_DIR / "all_queries_raw_results.csv"
    summary_path = RESULTS_DIR / "benchmark_summary.csv"

    if not raw_path.exists() or not summary_path.exists():
        print(f"[ERROR] Result files not found in {RESULTS_DIR}. Please run Experiment 08 first.")
        return

    print("Generating publication visualizations...")
    df_raw = pd.read_csv(raw_path)
    df_summary = pd.read_csv(summary_path)

    plot_recall_vs_selectivity(df_raw)
    plot_recall_vs_latency_tradeoff(df_summary)
    plot_qps_comparison(df_summary)
    plot_overfetch_sensitivity(df_summary)
    print("\n[OK] All publication figures generated successfully.")


if __name__ == "__main__":
    generate_all_plots()
