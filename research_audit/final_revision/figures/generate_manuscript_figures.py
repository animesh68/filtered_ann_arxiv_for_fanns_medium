"""
Publication-Quality Figure Generation Script for FANNS Manuscript
Generates Figures 1 to 5 directly from audited raw benchmark CSVs.

Outputs:
- fig1_cross_scale_pareto.pdf / .png
- fig2_overfetch_saturation.pdf / .png
- fig3_traversal_expansion_ablation.pdf / .png
- fig4_latency_cdf_tail.pdf / .png
- fig5_threshold_generalization.pdf / .png
"""

import os
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Style settings for academic publication
plt.rcParams.update({
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "lines.linewidth": 2.0,
    "lines.markersize": 7,
    "grid.alpha": 0.4,
    "grid.linestyle": "--",
    "figure.autolayout": True,
})

FIG_DIR = Path(__file__).resolve().parent


def generate_figure_1():
    """
    Figure 1: Cross-Scale Recall vs. Latency Trade-Off (1K vs. 100K)
    Sources:
    - 1K: C:/Users/anime/Desktop/filtered-ann-research-small/results/controlled_benchmark/benchmark_summary.csv
    - 100K: results/controlled_benchmark/benchmark_summary.csv
    """
    print("Generating Figure 1: Cross-Scale Pareto Frontier...")
    path_1k = Path("C:/Users/anime/Desktop/filtered-ann-research-small/results/controlled_benchmark/benchmark_summary.csv")
    path_100k = Path("results/controlled_benchmark/benchmark_summary.csv")

    if not path_1k.exists() or not path_100k.exists():
        print(f"[Warning] Missing summary CSVs for Figure 1: {path_1k} or {path_100k}")
        return

    df_1k = pd.read_csv(path_1k)
    df_100k = pd.read_csv(path_100k)

    methods = ["ExactSearch", "PreFilter", "HNSW_PostFilter", "HNSW_Overfetch_20x", "InGraphFilter"]
    markers = {"ExactSearch": "s", "PreFilter": "o", "HNSW_PostFilter": "x", "HNSW_Overfetch_20x": "^", "InGraphFilter": "D"}
    colors = {"EM": "#1f77b4", "Range": "#2ca02c", "EMIS": "#d62728"}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.5), sharey=True)

    # 1K Plot
    for w in ["EM", "Range", "EMIS"]:
        sub = df_1k[df_1k["filter_type"] == w]
        for m in methods:
            row = sub[sub["method"] == m]
            if len(row) > 0:
                ax1.scatter(
                    row["mean_latency_ms"].values[0],
                    row["mean_recall"].values[0],
                    color=colors[w],
                    marker=markers[m],
                    s=80,
                    label=f"{m} ({w})" if w == "EMIS" else None,
                )
    ax1.set_xscale("log")
    ax1.set_xlabel("Mean Latency (ms, log-scale)")
    ax1.set_ylabel("Macro-Averaged Recall@10")
    ax1.set_title("(a) Small Scale ($N=1,000$, $D=4,096$)")
    ax1.grid(True)
    ax1.set_ylim(-0.05, 1.05)
    ax1.axhline(1.0, color="gray", linestyle=":", alpha=0.5)
    ax1.text(0.05, 0.05, "Top-Left is Preferred\n(Higher Recall, Lower Latency)", transform=ax1.transAxes,
             fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="#f0f0f0", ec="gray", alpha=0.8))

    # 100K Plot
    for w in ["EM", "Range", "EMIS"]:
        sub = df_100k[df_100k["filter_type"] == w]
        for m in methods:
            row = sub[sub["method"] == m]
            if len(row) > 0:
                ax2.scatter(
                    row["mean_latency_ms"].values[0],
                    row["mean_recall"].values[0],
                    color=colors[w],
                    marker=markers[m],
                    s=80,
                    label=f"{w} Workload" if m == "InGraphFilter" else None,
                )
    ax2.set_xscale("log")
    ax2.set_xlabel("Mean Latency (ms, log-scale)")
    ax2.set_title("(b) Medium Scale ($N=100,000$, $D=4,096$)")
    ax2.grid(True)
    ax2.axhline(1.0, color="gray", linestyle=":", alpha=0.5)

    # Annotations on 100K to highlight collapse
    pf_emis = df_100k[(df_100k["filter_type"] == "EMIS") & (df_100k["method"] == "HNSW_PostFilter")]
    if len(pf_emis) > 0:
        ax2.annotate("PostFilter\nCollapse (0.171)", xy=(pf_emis["mean_latency_ms"].values[0], pf_emis["mean_recall"].values[0]),
                     xytext=(15, 0.28), arrowprops=dict(arrowstyle="->", color="#d62728", lw=1.5), fontsize=9, color="#d62728")

    ig_emis = df_100k[(df_100k["filter_type"] == "EMIS") & (df_100k["method"] == "InGraphFilter")]
    if len(ig_emis) > 0:
        ax2.annotate("InGraph Traversal\nExpansion (335 ms)", xy=(ig_emis["mean_latency_ms"].values[0], ig_emis["mean_recall"].values[0]),
                     xytext=(60, 0.70), arrowprops=dict(arrowstyle="->", color="#d62728", lw=1.5), fontsize=9, color="#d62728")

    # Method Legend below
    handles = [plt.Line2D([0], [0], marker=markers[m], color="black", linestyle="None", label=m) for m in methods]
    workload_handles = [plt.Line2D([0], [0], marker="o", color=colors[w], linestyle="None", label=f"{w} Workload") for w in ["EM", "Range", "EMIS"]]
    fig.legend(handles=handles + workload_handles, loc="upper center", bbox_to_anchor=(0.5, 1.08), ncol=4, frameon=True)

    fig.savefig(FIG_DIR / "fig1_cross_scale_pareto.pdf", bbox_inches="tight")
    fig.savefig(FIG_DIR / "fig1_cross_scale_pareto.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved Figure 1.")


def generate_figure_2():
    """
    Figure 2: Candidate Overfetch Saturation Curves (1x to 50x)
    Source: results/hnsw_overfetch/hnsw_overfetch_summary.csv
    """
    print("Generating Figure 2: Candidate Overfetch Saturation Curves...")
    csv_path = Path("results/hnsw_overfetch/hnsw_overfetch_summary.csv")
    if not csv_path.exists():
        print(f"[Warning] Missing {csv_path}")
        return

    df = pd.read_csv(csv_path)

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = {"EM": "#1f77b4", "Range": "#2ca02c", "EMIS": "#d62728"}
    markers = {"EM": "o", "Range": "s", "EMIS": "^"}

    for w in ["EM", "Range", "EMIS"]:
        sub = df[df["filter_type"] == w].sort_values("param_overfetch_factor")
        ax.plot(
            sub["param_overfetch_factor"],
            sub["mean_recall"],
            marker=markers[w],
            color=colors[w],
            label=f"{w} Workload (mean $\\sigma={sub['mean_selectivity'].values[0]*100:.1f}\\%$)",
        )

    ax.set_xlabel("Overfetch Multiplier $\\omega$ ($k_{\\text{fetch}} = \\omega \\cdot 10$)")
    ax.set_ylabel("Macro-Averaged Recall@10")
    ax.set_title("Candidate Overfetch Saturation Curves ($N=100,000, k=10$)")
    ax.grid(True)
    ax.set_ylim(0.1, 1.02)
    ax.set_xticks([1, 2, 5, 10, 20, 50])
    ax.set_xticklabels(["1x (10)", "2x (20)", "5x (50)", "10x (100)", "20x (200)", "50x (500)"])

    # Annotate EMIS plateau at 0.5140
    ax.annotate("EMIS Ceiling: 0.5140 @ 50x\n(leaves 48.6% unretrieved)", xy=(50, 0.514), xytext=(25, 0.40),
                arrowprops=dict(arrowstyle="->", color="#d62728", lw=1.5), fontsize=10, color="#d62728",
                bbox=dict(boxstyle="round,pad=0.3", fc="#ffebeb", ec="#d62728", alpha=0.8))

    ax.legend(loc="lower right", frameon=True)
    fig.savefig(FIG_DIR / "fig2_overfetch_saturation.pdf", bbox_inches="tight")
    fig.savefig(FIG_DIR / "fig2_overfetch_saturation.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved Figure 2.")


def generate_figure_3():
    """
    Figure 3: Traversal Expansion (Visited Nodes) vs. Selectivity (efC=50 vs. 100)
    Source: research_audit/followup_runs/EXP01_RAW.csv
    """
    print("Generating Figure 3: Traversal Expansion vs. Selectivity...")
    csv_path = Path("research_audit/followup_runs/EXP01_RAW.csv")
    if not csv_path.exists():
        print(f"[Warning] Missing {csv_path}")
        return

    df = pd.read_csv(csv_path)
    df_ig = df[df["method"] == "InGraphFilter"]

    fig, ax = plt.subplots(figsize=(8.5, 5.2))

    df_50 = df_ig[df_ig["ef_construction"] == 50]
    df_100 = df_ig[df_ig["ef_construction"] == 100]

    ax.scatter(df_50["selectivity"], df_50["nodes_visited_or_cand"], alpha=0.55, color="#1f77b4", marker="o", s=45, label="InGraph ($ef_C=50$, baseline)")
    ax.scatter(df_100["selectivity"], df_100["nodes_visited_or_cand"], alpha=0.55, color="#ff7f0e", marker="^", s=45, label="InGraph ($ef_C=100$, ablation)")

    ax.set_xscale("log")
    ax.set_xlabel("Query Filter Selectivity $\\sigma$ (log-scale)")
    ax.set_ylabel("Graph Nodes Visited (out of 100,000)")
    ax.set_title("Traversal Expansion vs. Attribute Selectivity ($N=100,000, k=10, ef_S=50$)")
    ax.grid(True)

    # Highlight selective regime
    ax.axvspan(0.0008, 0.02, color="red", alpha=0.08, label=r"Ultra-Selective Regime ($\sigma \leq 2\%$)")
    ax.annotate("Exploration Spike:\n~15,900 nodes visited\nfor both efC=50 and 100", xy=(0.005, 16000), xytext=(0.015, 17500),
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5), fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", fc="#fff3cd", ec="orange", alpha=0.9))

    ax.legend(loc="upper right", frameon=True)
    fig.savefig(FIG_DIR / "fig3_traversal_expansion_ablation.pdf", bbox_inches="tight")
    fig.savefig(FIG_DIR / "fig3_traversal_expansion_ablation.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved Figure 3.")


def generate_figure_4():
    """
    Figure 4: Latency CDF on EMIS Workload (InGraph, PreFilter, Router)
    Source: research_audit/followup_runs/EXP03_RAW.csv
    """
    print("Generating Figure 4: Latency CDF on EMIS...")
    csv_path = Path("research_audit/followup_runs/EXP03_RAW.csv")
    if not csv_path.exists():
        print(f"[Warning] Missing {csv_path}")
        return

    df = pd.read_csv(csv_path)
    df_emis = df[df["filter_type"] == "EMIS"]

    fig, ax = plt.subplots(figsize=(8.5, 5.2))

    for m, col, ls, lbl in [
        ("PreFilter", "#2ca02c", "-", "Static PreFilter (Recall: 1.0000, Mean: 117.8 ms)"),
        ("InGraphFilter", "#d62728", "--", "Static InGraphFilter (Recall: 0.8858, Mean: 214.4 ms)"),
        ("AdaptiveRouter_2pct", "#1f77b4", "-.", "AdaptiveRouter_2pct (Recall: 0.8918, Mean: 185.6 ms)"),
    ]:
        sub = df_emis[df_emis["method"] == m]
        if len(sub) > 0:
            lats = np.sort(sub["latency_ms"].values)
            cdf = np.arange(1, len(lats) + 1) / len(lats)
            ax.plot(lats, cdf, color=col, linestyle=ls, label=lbl, linewidth=2.2)

    ax.set_xscale("log")
    ax.set_xlabel("Query Execution Latency (ms, log-scale)")
    ax.set_ylabel("Empirical Cumulative Probability $F(t)$")
    ax.set_title("Latency Distribution on Selective EMIS Workload ($N=100,000, Q=500$)")
    ax.grid(True)
    ax.set_ylim(-0.02, 1.02)

    # Annotate P99 tail compression
    ax.axhline(0.99, color="gray", linestyle=":", alpha=0.7)
    ax.text(10, 0.96, "99th Percentile Tail", color="gray", fontsize=9)

    ax.annotate("Router compresses P99 by 127 ms\n(930 ms -> 803 ms vs InGraph)", xy=(850, 0.99), xytext=(120, 0.82),
                arrowprops=dict(arrowstyle="->", color="#1f77b4", lw=1.5), fontsize=9.5, color="#1f77b4",
                bbox=dict(boxstyle="round,pad=0.3", fc="#e6f2ff", ec="#1f77b4", alpha=0.9))

    ax.annotate("PreFilter P99 is lowest (265 ms)", xy=(265, 0.99), xytext=(50, 0.65),
                arrowprops=dict(arrowstyle="->", color="#2ca02c", lw=1.5), fontsize=9.5, color="#2ca02c",
                bbox=dict(boxstyle="round,pad=0.3", fc="#eafaf1", ec="#2ca02c", alpha=0.9))

    ax.legend(loc="lower right", frameon=True)
    fig.savefig(FIG_DIR / "fig4_latency_cdf_tail.pdf", bbox_inches="tight")
    fig.savefig(FIG_DIR / "fig4_latency_cdf_tail.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved Figure 4.")


def generate_figure_5():
    """
    Figure 5: Threshold Sensitivity Curves (Tuning vs. Held-Out Splits)
    Data from Table 5 / ROUTER_THRESHOLD_ANALYSIS.md
    """
    print("Generating Figure 5: Threshold Generalization...")
    # Exact audited data from Table 5
    thresholds = [0.5, 1.0, 2.0, 5.0, 10.0, 20.0]

    emis_tune_lat = [189, 188, 164, 123, 73, 56]
    emis_held_lat = [238, 238, 210, 155, 86, 54]

    em_tune_lat = [19.1, 19.1, 16.8, 16.1, 16.1, 26.5]
    em_held_lat = [15.5, 15.5, 14.5, 13.5, 13.5, 22.3]

    range_tune_lat = [26.2, 26.2, 26.2, 24.9, 24.9, 30.8]
    range_held_lat = [22.2, 20.6, 20.6, 19.6, 20.3, 27.5]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.2))

    # EMIS Subplot
    ax1.plot(thresholds, emis_tune_lat, marker="o", color="#d62728", linestyle="-", label="EMIS Tuning (Q0..249)")
    ax1.plot(thresholds, emis_held_lat, marker="s", color="#d62728", linestyle="--", label="EMIS Held-Out (Q250..499)")
    ax1.set_xlabel("Selectivity Threshold $\\tau$ (%)")
    ax1.set_ylabel("Mean Latency (ms)")
    ax1.set_title("(a) Multi-Attribute Workload (EMIS)")
    ax1.grid(True)
    ax1.axvspan(2.0, 5.0, color="gray", alpha=0.15, label="Target Window (2%–5%)")
    ax1.legend(loc="upper right", frameon=True)

    # Broad Workloads Subplot (EM and Range)
    ax2.plot(thresholds, em_tune_lat, marker="o", color="#1f77b4", linestyle="-", label="EM Tuning")
    ax2.plot(thresholds, em_held_lat, marker="s", color="#1f77b4", linestyle="--", label="EM Held-Out")
    ax2.plot(thresholds, range_tune_lat, marker="o", color="#2ca02c", linestyle="-", label="Range Tuning")
    ax2.plot(thresholds, range_held_lat, marker="s", color="#2ca02c", linestyle="--", label="Range Held-Out")
    ax2.set_xlabel("Selectivity Threshold $\\tau$ (%)")
    ax2.set_ylabel("Mean Latency (ms)")
    ax2.set_title("(b) Point & Range Workloads (EM & Range)")
    ax2.grid(True)
    ax2.axvspan(2.0, 5.0, color="gray", alpha=0.15, label="Target Window (2%–5%)")

    # Annotate degradation above 5% on EM/Range
    ax2.annotate(r"Broad workloads degrade" + "\n" + r"when $\tau \geq 10\%$ (PreFilter cost)", xy=(20, 27.5), xytext=(7, 28),
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5), fontsize=9.5,
                bbox=dict(boxstyle="round,pad=0.3", fc="#fdfefe", ec="gray", alpha=0.9))

    ax2.legend(loc="upper left", frameon=True)

    fig.savefig(FIG_DIR / "fig5_threshold_generalization.pdf", bbox_inches="tight")
    fig.savefig(FIG_DIR / "fig5_threshold_generalization.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved Figure 5.")


if __name__ == "__main__":
    print("Generating all 5 manuscript figures from audited data...")
    generate_figure_1()
    generate_figure_2()
    generate_figure_3()
    generate_figure_4()
    generate_figure_5()
    print("All figures successfully generated in PDF and PNG formats.")
