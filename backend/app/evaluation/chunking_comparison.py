"""
Chunking Comparison Tool
========================

Compare semantic neural chunking vs traditional fixed chunking.
Provides metrics, visualizations, and quality assessments.
"""

import logging
import json
from typing import Dict, List, Any, Tuple
from pathlib import Path
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class ChunkingComparator:
    """Compare different chunking strategies and measure their effectiveness."""
    
    def __init__(self, output_dir: str = "./evaluation_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = []
    
    def compare_single_document(
        self,
        pdf_path: str,
        semantic_result: Dict[str, Any],
        traditional_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare semantic vs traditional chunking for a single document.
        
        Args:
            pdf_path: Path to the PDF file
            semantic_result: Processing result with semantic chunking
            traditional_result: Processing result with traditional chunking
            
        Returns:
            Dictionary of comparison metrics
        """
        comparison = {
            'document': Path(pdf_path).name,
            'timestamp': datetime.now().isoformat(),
            'semantic': self._extract_metrics(semantic_result, 'semantic'),
            'traditional': self._extract_metrics(traditional_result, 'traditional'),
        }
        
        # Calculate improvements
        comparison['improvements'] = self._calculate_improvements(
            comparison['semantic'],
            comparison['traditional']
        )
        
        self.results.append(comparison)
        logger.info(f"Comparison complete for {comparison['document']}")
        
        return comparison
    
    def _extract_metrics(self, result: Dict[str, Any], method: str) -> Dict[str, Any]:
        """Extract relevant metrics from processing result."""
        summary = result.get('processing_summary', {})
        chunking_params = result.get('chunking_params', {})
        
        # Get text chunks
        text_chunks = []
        if 'separated_elements' in result:
            texts = result['separated_elements'].get('texts', [])
            text_chunks = [str(t) for t in texts]
        elif 'text_content' in result:
            text_chunks = result['text_content']
        
        # Calculate metrics
        num_chunks = len(text_chunks)
        chunk_sizes = [len(chunk) for chunk in text_chunks]
        
        metrics = {
            'method': method,
            'num_chunks': num_chunks,
            'avg_chunk_size': np.mean(chunk_sizes) if chunk_sizes else 0,
            'median_chunk_size': np.median(chunk_sizes) if chunk_sizes else 0,
            'std_chunk_size': np.std(chunk_sizes) if chunk_sizes else 0,
            'min_chunk_size': min(chunk_sizes) if chunk_sizes else 0,
            'max_chunk_size': max(chunk_sizes) if chunk_sizes else 0,
            'total_characters': sum(chunk_sizes),
            'chunking_params': chunking_params
        }
        
        # Extract semantic-specific metrics if available
        if method == 'semantic' and chunking_params.get('chunking_method') == 'semantic_neural':
            # Try to get coherence scores from chunks
            coherence_scores = []
            if 'raw_chunks' in result:
                for chunk in result['raw_chunks']:
                    if hasattr(chunk, 'metadata') and hasattr(chunk.metadata, 'coherence_score'):
                        coherence_scores.append(chunk.metadata.coherence_score)
            
            if coherence_scores:
                metrics['avg_coherence'] = float(np.mean(coherence_scores))
                metrics['min_coherence'] = float(np.min(coherence_scores))
                metrics['max_coherence'] = float(np.max(coherence_scores))
        
        return metrics
    
    def _calculate_improvements(
        self,
        semantic_metrics: Dict[str, Any],
        traditional_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate improvement metrics."""
        improvements = {}
        
        # Chunk count difference
        sem_chunks = semantic_metrics['num_chunks']
        trad_chunks = traditional_metrics['num_chunks']
        improvements['chunk_count_diff'] = sem_chunks - trad_chunks
        improvements['chunk_count_pct'] = (
            ((sem_chunks - trad_chunks) / trad_chunks * 100)
            if trad_chunks > 0 else 0
        )
        
        # Size consistency (lower std is better)
        sem_std = semantic_metrics['std_chunk_size']
        trad_std = traditional_metrics['std_chunk_size']
        improvements['consistency_improvement'] = (
            ((trad_std - sem_std) / trad_std * 100)
            if trad_std > 0 else 0
        )
        
        # Coherence (semantic only)
        if 'avg_coherence' in semantic_metrics:
            improvements['avg_coherence'] = semantic_metrics['avg_coherence']
            improvements['coherence_interpretation'] = self._interpret_coherence(
                semantic_metrics['avg_coherence']
            )
        
        return improvements
    
    def _interpret_coherence(self, score: float) -> str:
        """Interpret coherence score."""
        if score >= 0.8:
            return "Excellent - Very coherent chunks"
        elif score >= 0.7:
            return "Good - Well-defined boundaries"
        elif score >= 0.6:
            return "Fair - Moderate coherence"
        else:
            return "Poor - May need tuning"
    
    def generate_report(self, output_file: str = None) -> str:
        """
        Generate a comprehensive comparison report.
        
        Args:
            output_file: Optional file path to save report
            
        Returns:
            Report as formatted string
        """
        if not self.results:
            return "No comparison results available."
        
        report_lines = [
            "=" * 80,
            "SEMANTIC vs TRADITIONAL CHUNKING COMPARISON REPORT",
            "=" * 80,
            f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Documents Analyzed: {len(self.results)}\n",
        ]
        
        # Summary statistics
        all_semantic = [r['semantic'] for r in self.results]
        all_traditional = [r['traditional'] for r in self.results]
        all_improvements = [r['improvements'] for r in self.results]
        
        report_lines.extend([
            "\n" + "-" * 80,
            "OVERALL SUMMARY",
            "-" * 80,
        ])
        
        # Average chunk counts
        avg_sem_chunks = np.mean([s['num_chunks'] for s in all_semantic])
        avg_trad_chunks = np.mean([t['num_chunks'] for t in all_traditional])
        report_lines.append(f"\nAverage Chunks per Document:")
        report_lines.append(f"  Semantic:     {avg_sem_chunks:.1f}")
        report_lines.append(f"  Traditional:  {avg_trad_chunks:.1f}")
        report_lines.append(f"  Difference:   {avg_sem_chunks - avg_trad_chunks:+.1f} ({(avg_sem_chunks/avg_trad_chunks - 1)*100:+.1f}%)")
        
        # Average chunk sizes
        avg_sem_size = np.mean([s['avg_chunk_size'] for s in all_semantic])
        avg_trad_size = np.mean([t['avg_chunk_size'] for t in all_traditional])
        report_lines.append(f"\nAverage Chunk Size (characters):")
        report_lines.append(f"  Semantic:     {avg_sem_size:.0f}")
        report_lines.append(f"  Traditional:  {avg_trad_size:.0f}")
        
        # Consistency improvement
        avg_consistency = np.mean([i['consistency_improvement'] for i in all_improvements])
        report_lines.append(f"\nConsistency Improvement: {avg_consistency:+.1f}%")
        
        # Coherence scores (semantic only)
        coherence_scores = [s.get('avg_coherence', 0) for s in all_semantic if 'avg_coherence' in s]
        if coherence_scores:
            avg_coherence = np.mean(coherence_scores)
            report_lines.append(f"\nSemantic Coherence Score: {avg_coherence:.3f}")
            report_lines.append(f"  Interpretation: {self._interpret_coherence(avg_coherence)}")
        
        # Individual document results
        report_lines.extend([
            "\n" + "-" * 80,
            "INDIVIDUAL DOCUMENT RESULTS",
            "-" * 80,
        ])
        
        for result in self.results:
            report_lines.append(f"\n📄 {result['document']}")
            report_lines.append(f"  Semantic:     {result['semantic']['num_chunks']} chunks (avg: {result['semantic']['avg_chunk_size']:.0f} chars)")
            report_lines.append(f"  Traditional:  {result['traditional']['num_chunks']} chunks (avg: {result['traditional']['avg_chunk_size']:.0f} chars)")
            
            if 'avg_coherence' in result['semantic']:
                report_lines.append(f"  Coherence:    {result['semantic']['avg_coherence']:.3f}")
        
        report_lines.append("\n" + "=" * 80)
        
        report_text = "\n".join(report_lines)
        
        # Save to file if requested
        if output_file:
            output_path = self.output_dir / output_file
            with open(output_path, 'w') as f:
                f.write(report_text)
            logger.info(f"Report saved to: {output_path}")
        
        return report_text
    
    def save_json_results(self, output_file: str = "comparison_results.json"):
        """Save detailed results as JSON."""
        output_path = self.output_dir / output_file
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        logger.info(f"JSON results saved to: {output_path}")
        return str(output_path)


def quick_comparison_summary(semantic_result: Dict, traditional_result: Dict) -> str:
    """Generate a quick text summary of comparison."""
    sem_chunks = len(semantic_result.get('text_content', []))
    trad_chunks = len(traditional_result.get('text_content', []))
    
    summary = [
        "\n🧠 SEMANTIC vs 📐 TRADITIONAL CHUNKING",
        "=" * 50,
        f"Semantic:     {sem_chunks} chunks",
        f"Traditional:  {trad_chunks} chunks",
        f"Difference:   {sem_chunks - trad_chunks:+d} chunks ({(sem_chunks/trad_chunks - 1)*100:+.1f}%)" if trad_chunks > 0 else "N/A",
    ]
    
    return "\n".join(summary)
