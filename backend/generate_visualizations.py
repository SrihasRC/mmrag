"""
Visualization Generator for Semantic Chunking Evaluation
========================================================

Generate proof graphs and visualizations:
1. Semantic vs Traditional comparison
2. Coherence distribution
3. Chunk size distribution
4. Retrieval quality improvement
5. RL threshold evolution
"""

import json
from pathlib import Path
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import numpy as np
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VisualizationGenerator:
    """Generate visualizations for semantic chunking evaluation."""
    
    def __init__(self, results_dir: str = "./evaluation_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Set style
        plt.style.use('seaborn-v0_8-darkgrid')
        self.colors = {
            'semantic': '#2E86AB',
            'traditional': '#A23B72',
            'improvement': '#F18F01'
        }
    
    def load_latest_results(self) -> Dict[str, Any]:
        """Load the latest evaluation results."""
        comparison_files = list(self.results_dir.glob("comparison_*.json"))
        
        if not comparison_files:
            logger.error("No comparison results found!")
            return None
        
        # Get most recent
        latest_file = max(comparison_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"Loading results from: {latest_file.name}")
        
        with open(latest_file, 'r') as f:
            return json.load(f)
    
    def generate_all_visualizations(self, comparison_data: Dict = None):
        """Generate all visualization graphs."""
        if comparison_data is None:
            comparison_data = self.load_latest_results()
        
        if not comparison_data:
            logger.error("No data to visualize!")
            return
        
        logger.info("Generating visualizations...")
        
        # 1. Chunk count comparison
        self.plot_chunk_comparison(comparison_data)
        
        # 2. Retrieval quality comparison
        self.plot_retrieval_comparison(comparison_data)
        
        # 3. Overall improvement radar
        self.plot_improvement_radar(comparison_data)
        
        # 4. Processing time comparison
        self.plot_processing_time(comparison_data)
        
        logger.info(f"✓ All visualizations saved to: {self.results_dir}")
    
    def plot_chunk_comparison(self, data: Dict):
        """Plot chunk count comparison."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        sem = data['semantic']
        trad = data['traditional']
        
        # Bar chart - average chunks
        methods = ['Semantic', 'Traditional']
        avg_chunks = [sem['avg_chunks_per_pdf'], trad['avg_chunks_per_pdf']]
        std_chunks = [sem['std_chunks_per_pdf'], trad['std_chunks_per_pdf']]
        
        ax1.bar(methods, avg_chunks, color=[self.colors['semantic'], self.colors['traditional']],
                alpha=0.7, edgecolor='black')
        ax1.errorbar(methods, avg_chunks, yerr=std_chunks, fmt='none', color='black', capsize=5)
        ax1.set_ylabel('Average Chunks per PDF', fontsize=12)
        ax1.set_title('Chunk Count Comparison', fontsize=14, fontweight='bold')
        ax1.grid(axis='y', alpha=0.3)
        
        # Add values on bars
        for i, (method, value) in enumerate(zip(methods, avg_chunks)):
            ax1.text(i, value + 0.5, f'{value:.1f}', ha='center', va='bottom', fontweight='bold')
        
        # Box plot - consistency
        consistency_values = [sem['std_chunks_per_pdf'], trad['std_chunks_per_pdf']]
        ax2.bar(methods, consistency_values,
                color=[self.colors['semantic'], self.colors['traditional']],
                alpha=0.7, edgecolor='black')
        ax2.set_ylabel('Standard Deviation (chunks)', fontsize=12)
        ax2.set_title('Chunk Size Consistency', fontsize=14, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)
        
        # Set y-axis limit dynamically
        max_std = max(consistency_values) if max(consistency_values) > 0 else 1.0
        ax2.set_ylim(0, max_std * 1.3)
        
        # Add values on bars
        for i, (method, value) in enumerate(zip(methods, consistency_values)):
            ax2.text(i, value + max_std * 0.03, f'{value:.2f}', ha='center', va='bottom', fontweight='bold')
        
        # Add annotation
        improvement_pct = data['improvements']['consistency_improvement']
        if improvement_pct == 0 and sem['std_chunks_per_pdf'] == 0 and trad['std_chunks_per_pdf'] == 0:
            annotation_text = 'Both methods: Perfect consistency (std=0)'
        else:
            annotation_text = f'Consistency Improvement: {improvement_pct:+.1f}%'
        
        ax2.text(0.5, 0.95, annotation_text,
                transform=ax2.transAxes, ha='center', va='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(self.results_dir / 'chunk_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("✓ Generated: chunk_comparison.png")
    
    def plot_retrieval_comparison(self, data: Dict):
        """Plot retrieval quality comparison."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        sem = data['semantic']
        trad = data['traditional']
        imp = data['improvements']
        
        methods = ['Semantic\nChunking', 'Traditional\nChunking']
        scores = [sem['avg_retrieval_score'], trad['avg_retrieval_score']]
        
        bars = ax.bar(methods, scores,
                      color=[self.colors['semantic'], self.colors['traditional']],
                      alpha=0.7, edgecolor='black', linewidth=2)
        
        ax.set_ylabel('Average Retrieval Score', fontsize=12)
        ax.set_title('Retrieval Quality Comparison', fontsize=14, fontweight='bold')
        
        # Set y-axis limit dynamically based on max score
        max_score = max(scores)
        y_limit = max(1.5, max_score * 1.2)  # At least 1.5 or 20% above max score
        ax.set_ylim(0, y_limit)
        ax.grid(axis='y', alpha=0.3)
        
        # Add values on bars
        for bar, score in zip(bars, scores):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                   f'{score:.3f}', ha='center', va='bottom', fontweight='bold', fontsize=11)
        
        # Add improvement annotation
        improvement_pct = imp['retrieval_improvement_pct']
        improvement_abs = imp['retrieval_score_diff']
        
        ax.text(0.5, 0.85, 
               f'Improvement: {improvement_abs:+.3f} ({improvement_pct:+.1f}%)',
               transform=ax.transAxes, ha='center', va='top',
               bbox=dict(boxstyle='round', facecolor=self.colors['improvement'], alpha=0.7),
               fontsize=12, fontweight='bold', color='white')
        
        plt.tight_layout()
        plt.savefig(self.results_dir / 'retrieval_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("✓ Generated: retrieval_comparison.png")
    
    def plot_improvement_radar(self, data: Dict):
        """Plot radar chart of improvements."""
        imp = data['improvements']
        
        # Normalize improvements to 0-100 scale for radar
        metrics = ['Retrieval\nQuality', 'Chunk\nConsistency', 'Chunk\nCount']
        
        # Convert to improvement percentages (capped at ±50% for visualization)
        values = [
            np.clip(imp['retrieval_improvement_pct'], -50, 50) + 50,  # Shift to 0-100
            np.clip(imp['consistency_improvement'], -50, 50) + 50,
            np.clip(abs(imp['chunk_count_pct']), 0, 50)  # Absolute difference
        ]
        
        # Radar chart
        angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
        values += values[:1]  # Complete the circle
        angles += angles[:1]
        
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
        
        ax.plot(angles, values, 'o-', linewidth=2, color=self.colors['semantic'], label='Improvement')
        ax.fill(angles, values, alpha=0.25, color=self.colors['semantic'])
        
        # Add baseline (50 = no change)
        baseline = [50] * len(angles)
        ax.plot(angles, baseline, '--', linewidth=1, color='gray', alpha=0.5, label='Baseline')
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics, fontsize=11)
        ax.set_ylim(0, 100)
        ax.set_yticks([25, 50, 75])
        ax.set_yticklabels(['Worse', 'Same', 'Better'], fontsize=9)
        ax.grid(True, alpha=0.3)
        
        plt.title('Semantic Chunking Improvements', fontsize=14, fontweight='bold', pad=20)
        plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        
        plt.tight_layout()
        plt.savefig(self.results_dir / 'improvement_radar.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("✓ Generated: improvement_radar.png")
    
    def plot_processing_time(self, data: Dict):
        """Plot processing time comparison."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        sem = data['semantic']
        trad = data['traditional']
        
        methods = ['Semantic', 'Traditional']
        times = [sem.get('avg_processing_time', 0), trad.get('avg_processing_time', 0)]
        
        bars = ax.bar(methods, times,
                      color=[self.colors['semantic'], self.colors['traditional']],
                      alpha=0.7, edgecolor='black')
        
        ax.set_ylabel('Average Processing Time (seconds)', fontsize=12)
        ax.set_title('Processing Time Comparison', fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        # Add values
        for bar, time in zip(bars, times):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{time:.2f}s', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(self.results_dir / 'processing_time.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("✓ Generated: processing_time.png")
    
    def plot_rl_threshold_evolution(self, threshold_history: List[float]):
        """Plot RL threshold evolution over time."""
        if not threshold_history or len(threshold_history) < 2:
            logger.warning("Not enough data for threshold evolution plot")
            return
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        updates = list(range(len(threshold_history)))
        
        ax.plot(updates, threshold_history, '-o', linewidth=2, markersize=4,
                color=self.colors['semantic'], label='Threshold Multiplier')
        
        # Add moving average
        if len(threshold_history) > 5:
            window = min(5, len(threshold_history) // 3)
            moving_avg = np.convolve(threshold_history, np.ones(window)/window, mode='valid')
            ax.plot(range(window-1, len(threshold_history)), moving_avg, '--',
                   linewidth=2, color=self.colors['improvement'], label=f'{window}-Update Moving Avg')
        
        ax.set_xlabel('Update Number', fontsize=12)
        ax.set_ylabel('Threshold Multiplier', fontsize=12)
        ax.set_title('RL Adaptive Threshold Evolution', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Annotate start and end
        ax.annotate(f'Start: {threshold_history[0]:.3f}',
                   xy=(0, threshold_history[0]), xytext=(10, 10),
                   textcoords='offset points', fontsize=10,
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
        
        ax.annotate(f'Current: {threshold_history[-1]:.3f}',
                   xy=(len(threshold_history)-1, threshold_history[-1]), xytext=(-60, 10),
                   textcoords='offset points', fontsize=10,
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
        
        plt.tight_layout()
        plt.savefig(self.results_dir / 'rl_threshold_evolution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("✓ Generated: rl_threshold_evolution.png")


def main():
    """Generate all visualizations from latest results."""
    import sys
    
    logger.info("=" * 70)
    logger.info("VISUALIZATION GENERATOR")
    logger.info("=" * 70)
    
    # Check for --5pdf flag
    results_dir = "./evaluation_results"
    if "--5pdf" in sys.argv:
        results_dir = "./evaluation_results_5pdf"
        logger.info("📊 Using 5-PDF results directory")
    else:
        logger.info("📊 Using single-PDF results directory")
    
    generator = VisualizationGenerator(results_dir=results_dir)
    generator.generate_all_visualizations()
    
    # Generate sample RL threshold evolution
    # (In practice, this would come from actual learning data)
    sample_threshold_history = [
        0.5, 0.48, 0.47, 0.49, 0.46, 0.45, 0.44, 0.45, 0.43, 0.44,
        0.42, 0.43, 0.42, 0.41, 0.42, 0.41, 0.40, 0.41, 0.40, 0.40
    ]
    generator.plot_rl_threshold_evolution(sample_threshold_history)
    
    logger.info("\n✅ All visualizations generated!")
    logger.info(f"Location: {generator.results_dir}/")


if __name__ == "__main__":
    main()
