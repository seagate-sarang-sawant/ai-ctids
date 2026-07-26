"""Visualize API evaluation results.

Creates plots and charts from evaluation JSON files.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)


def load_results(results_path: str) -> Dict:
    """Load evaluation results from JSON file."""
    with open(results_path, 'r') as f:
        return json.load(f)


def plot_metrics_comparison(results_files: List[str], output_path: str = None):
    """Plot comparison of metrics across different test runs."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('API Evaluation Metrics Comparison', fontsize=16, fontweight='bold')
    
    metrics_data = []
    labels = []
    
    for results_file in results_files:
        results = load_results(results_file)
        metrics_data.append(results['metrics'])
        # Extract label from filename
        label = Path(results_file).stem.replace('results_', '').replace('_', ' ').title()
        labels.append(label)
    
    # Accuracy comparison
    accuracies = [m['accuracy'] for m in metrics_data]
    axes[0, 0].bar(labels, accuracies, color='skyblue')
    axes[0, 0].set_title('Accuracy', fontweight='bold')
    axes[0, 0].set_ylabel('Score')
    axes[0, 0].set_ylim([0, 1.0])
    axes[0, 0].axhline(y=0.95, color='r', linestyle='--', label='Target (95%)')
    axes[0, 0].legend()
    axes[0, 0].tick_params(axis='x', rotation=45)
    
    # F1 scores comparison
    f1_macros = [m['f1_macro'] for m in metrics_data]
    f1_weighted = [m['f1_weighted'] for m in metrics_data]
    
    x = np.arange(len(labels))
    width = 0.35
    axes[0, 1].bar(x - width/2, f1_macros, width, label='F1 Macro', color='lightgreen')
    axes[0, 1].bar(x + width/2, f1_weighted, width, label='F1 Weighted', color='lightcoral')
    axes[0, 1].set_title('F1 Scores', fontweight='bold')
    axes[0, 1].set_ylabel('Score')
    axes[0, 1].set_ylim([0, 1.0])
    axes[0, 1].set_xticks(x)
    axes[0, 1].set_xticklabels(labels, rotation=45)
    axes[0, 1].axhline(y=0.85, color='r', linestyle='--', alpha=0.5)
    axes[0, 1].legend()
    
    # Precision vs Recall
    precisions = [m['precision_macro'] for m in metrics_data]
    recalls = [m['recall_macro'] for m in metrics_data]
    
    axes[1, 0].bar(x - width/2, precisions, width, label='Precision', color='orange')
    axes[1, 0].bar(x + width/2, recalls, width, label='Recall', color='purple')
    axes[1, 0].set_title('Precision vs Recall (Macro)', fontweight='bold')
    axes[1, 0].set_ylabel('Score')
    axes[1, 0].set_ylim([0, 1.0])
    axes[1, 0].set_xticks(x)
    axes[1, 0].set_xticklabels(labels, rotation=45)
    axes[1, 0].legend()
    
    # Summary table
    axes[1, 1].axis('off')
    table_data = []
    for label, metrics in zip(labels, metrics_data):
        table_data.append([
            label,
            f"{metrics['accuracy']:.3f}",
            f"{metrics['f1_macro']:.3f}",
            f"{metrics['precision_macro']:.3f}",
            f"{metrics['recall_macro']:.3f}"
        ])
    
    table = axes[1, 1].table(
        cellText=table_data,
        colLabels=['Test Set', 'Accuracy', 'F1', 'Precision', 'Recall'],
        cellLoc='center',
        loc='center',
        bbox=[0, 0, 1, 1]
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    
    # Style header
    for i in range(5):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Saved metrics comparison to {output_path}")
    else:
        plt.show()


def plot_inference_times(results_files: List[str], output_path: str = None):
    """Plot inference time statistics."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('Inference Time Analysis', fontsize=16, fontweight='bold')
    
    labels = []
    all_times = []
    
    for results_file in results_files:
        results = load_results(results_file)
        times = results.get('inference_times_ms', [])
        if times:
            all_times.append(times)
            label = Path(results_file).stem.replace('results_', '').replace('_', ' ').title()
            labels.append(label)
    
    if not all_times:
        logger.warning("No inference time data found")
        return
    
    # Box plot
    axes[0].boxplot(all_times, labels=labels)
    axes[0].set_title('Inference Time Distribution', fontweight='bold')
    axes[0].set_ylabel('Time (ms)')
    axes[0].axhline(y=20, color='g', linestyle='--', label='Target (20ms)')
    axes[0].axhline(y=50, color='r', linestyle='--', label='Warning (50ms)')
    axes[0].legend()
    axes[0].tick_params(axis='x', rotation=45)
    axes[0].grid(True, alpha=0.3)
    
    # Statistics comparison
    stats_data = []
    for times, label in zip(all_times, labels):
        stats_data.append({
            'Test Set': label,
            'Mean': np.mean(times),
            'Median': np.median(times),
            'Std': np.std(times),
            'P95': np.percentile(times, 95)
        })
    
    stats_df = pd.DataFrame(stats_data)
    
    x = np.arange(len(labels))
    width = 0.2
    
    axes[1].bar(x - 1.5*width, stats_df['Mean'], width, label='Mean', color='skyblue')
    axes[1].bar(x - 0.5*width, stats_df['Median'], width, label='Median', color='lightgreen')
    axes[1].bar(x + 0.5*width, stats_df['Std'], width, label='Std', color='orange')
    axes[1].bar(x + 1.5*width, stats_df['P95'], width, label='P95', color='lightcoral')
    
    axes[1].set_title('Inference Time Statistics', fontweight='bold')
    axes[1].set_ylabel('Time (ms)')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels, rotation=45)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Saved inference time plot to {output_path}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description="Visualize API evaluation results")
    parser.add_argument("--results", nargs="+", required=True,
                       help="Paths to result JSON files")
    parser.add_argument("--output-dir", type=str, default="./tests/api_evaluation",
                       help="Output directory for plots")
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Plot metrics comparison
    plot_metrics_comparison(
        args.results,
        output_path=os.path.join(args.output_dir, "metrics_comparison.png")
    )
    
    # Plot inference times
    plot_inference_times(
        args.results,
        output_path=os.path.join(args.output_dir, "inference_times.png")
    )
    
    logger.info("Visualization complete!")


if __name__ == "__main__":
    main()
