"""
Comprehensive Evaluation Suite for Semantic Chunking
===================================================

Evaluate semantic chunking with:
1. Test query sets (factual, conceptual, comparative)
2. Multi-PDF benchmark (11 PDFs in ref/pdf-dataset/)
3. Retrieval quality metrics
4. Comparison with traditional chunking
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
import logging
from datetime import datetime
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import UploadFile
from io import BytesIO
from app.services.multimodal_rag import multimodal_rag_service
from app.services.pdf_processor import pdf_processor
from app.evaluation.chunking_comparison import ChunkingComparator
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Test Query Sets
TEST_QUERIES = {
    'factual': [
        "What is the main dataset used in this paper?",
        "What is the accuracy or performance reported?",
        "How many parameters does the model have?",
        "What year was this published?",
        "Who are the authors of this work?",
    ],
    'conceptual': [
        "Explain the main methodology",
        "What is the key contribution of this work?",
        "Summarize the results and findings",
        "What problem does this research address?",
        "Describe the proposed approach",
    ],
    'comparative': [
        "How does this compare to previous work?",
        "What are the advantages over existing methods?",
        "What are the limitations of this approach?",
        "How does this improve upon the baseline?",
        "What makes this different from other solutions?",
    ]
}


class ComprehensiveEvaluator:
    """Comprehensive evaluation of semantic chunking on multiple PDFs."""
    
    def __init__(self, pdf_dir: str = "./ref/pdf-dataset", output_dir: str = "./evaluation_results"):
        self.pdf_dir = Path(pdf_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = []
        self.pdf_results = {}
        
        logger.info(f"Evaluator initialized: {self.pdf_dir}")
    
    async def evaluate_all_pdfs(
        self,
        use_semantic: bool = True,
        max_pdfs: int = None
    ) -> Dict[str, Any]:
        """
        Evaluate all PDFs in the dataset directory.
        
        Args:
            use_semantic: Use semantic chunking vs traditional
            max_pdfs: Maximum number of PDFs to process (None = all)
            
        Returns:
            Evaluation results dictionary
        """
        logger.info("=" * 70)
        logger.info(f"COMPREHENSIVE EVALUATION: semantic={use_semantic}")
        logger.info("=" * 70)
        
        # Get all PDFs
        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        if max_pdfs:
            pdf_files = pdf_files[:max_pdfs]
        
        logger.info(f"Found {len(pdf_files)} PDFs to evaluate")
        logger.info(f"PDF list: {[p.name for p in pdf_files]}")
        
        evaluation_results = {
            'timestamp': datetime.now().isoformat(),
            'use_semantic_chunking': use_semantic,
            'total_pdfs': len(pdf_files),
            'pdf_results': [],
            'aggregate_metrics': {}
        }
        
        for i, pdf_path in enumerate(pdf_files, 1):
            logger.info(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_path.name}")
            
            try:
                result = await self._evaluate_single_pdf(pdf_path, use_semantic)
                evaluation_results['pdf_results'].append(result)
                self.pdf_results[pdf_path.name] = result
                
            except Exception as e:
                logger.error(f"Error processing {pdf_path.name}: {e}")
                evaluation_results['pdf_results'].append({
                    'pdf_name': pdf_path.name,
                    'status': 'error',
                    'error': str(e)
                })
        
        # Calculate aggregate metrics
        evaluation_results['aggregate_metrics'] = self._calculate_aggregate_metrics(
            evaluation_results['pdf_results']
        )
        
        # Save results
        self._save_results(evaluation_results, use_semantic)
        
        return evaluation_results
    
    async def _evaluate_single_pdf(
        self,
        pdf_path: Path,
        use_semantic: bool
    ) -> Dict[str, Any]:
        """Evaluate a single PDF."""
        start_time = time.time()
        
        # Process PDF
        with open(pdf_path, 'rb') as f:
            file_content = f.read()
        
        # Create UploadFile object
        upload_file = UploadFile(
            filename=pdf_path.name,
            file=BytesIO(file_content)
        )
        
        # Process through pipeline
        try:
            processing_result = await multimodal_rag_service.process_pdf_complete(
                upload_file,
                save_content=False,
                use_semantic_chunking=use_semantic
            )
            
            pdf_id = processing_result['pdf_id']
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return {
                'pdf_name': pdf_path.name,
                'status': 'processing_failed',
                'error': str(e)
            }
        
        processing_time = time.time() - start_time
        
        # Extract processing info
        summary = processing_result['processing_summary']
        embedding_result = processing_result['embedding_result']
        
        # Get chunk count from the correct field
        num_chunks = summary.get('num_text_chunks', summary.get('texts_count', 0))
        
        result = {
            'pdf_name': pdf_path.name,
            'pdf_id': pdf_id,
            'status': 'success',
            'processing_time': processing_time,
            'num_chunks': num_chunks,
            'num_tables': summary.get('num_tables', summary.get('tables_count', 0)),
            'num_images': summary.get('num_images', summary.get('images_count', 0)),
            'embeddings_created': embedding_result.get('documents_added', 0),
            'chunking_method': summary.get('chunking_method', 'unknown'),
        }
        
        # Test retrieval quality with more discriminative scoring
        retrieval_scores = []
        query_details = []
        
        for query_type, queries in TEST_QUERIES.items():
            # Sample one query from each type
            query = queries[0]
            
            try:
                query_result = await multimodal_rag_service.query_rag(
                    question=query,
                    pdf_id=pdf_id,
                    top_k=3
                )
                
                # More nuanced scoring based on relevance
                # Use the similarity scores from retrieved documents
                retrieved_docs = query_result.get('retrieved_docs', [])
                if retrieved_docs:
                    # Average the similarity scores from metadata
                    doc_scores = []
                    for doc in retrieved_docs:
                        # Get score from metadata
                        score = doc.metadata.get('similarity_score', 0.5)
                        doc_scores.append(score)
                    score = float(np.mean(doc_scores)) if doc_scores else 0.5
                else:
                    score = 0.0
                
                retrieval_scores.append(score)
                query_details.append({
                    'query_type': query_type,
                    'query': query,
                    'score': score,
                    'docs_retrieved': len(retrieved_docs)
                })
                
            except Exception as e:
                logger.debug(f"Query '{query}' failed: {e}")
                retrieval_scores.append(0.0)
                query_details.append({
                    'query_type': query_type,
                    'query': query,
                    'score': 0.0,
                    'error': str(e)
                })
        
        result['avg_retrieval_score'] = float(np.mean(retrieval_scores)) if retrieval_scores else 0.0
        result['queries_tested'] = len(retrieval_scores)
        result['query_details'] = query_details
        
        # Get RL adaptive threshold stats if using semantic chunking
        if use_semantic:
            try:
                rl_stats = pdf_processor.semantic_chunker.get_adaptive_stats()
                result['rl_stats'] = rl_stats
            except Exception as e:
                logger.debug(f"Could not get RL stats: {e}")
                result['rl_stats'] = None
        
        logger.info(f"✓ {pdf_path.name}: {result['num_chunks']} chunks, retrieval={result['avg_retrieval_score']:.2f}")
        
        return result
    
    def _calculate_aggregate_metrics(self, pdf_results: List[Dict]) -> Dict[str, Any]:
        """Calculate aggregate metrics across all PDFs."""
        successful = [r for r in pdf_results if r.get('status') == 'success']
        
        if not successful:
            return {'success_rate': 0.0}
        
        metrics = {
            'success_rate': len(successful) / len(pdf_results),
            'avg_chunks_per_pdf': float(np.mean([r['num_chunks'] for r in successful])),
            'std_chunks_per_pdf': float(np.std([r['num_chunks'] for r in successful])),
            'total_chunks': sum(r['num_chunks'] for r in successful),
            'avg_retrieval_score': float(np.mean([r['avg_retrieval_score'] for r in successful])),
            'avg_processing_time': float(np.mean([r['processing_time'] for r in successful])),
            'total_processing_time': sum(r['processing_time'] for r in successful),
        }
        
        # Add RL statistics if available
        rl_stats_list = [r.get('rl_stats') for r in successful if r.get('rl_stats') is not None]
        if rl_stats_list:
            # Get the latest RL stats (from last PDF processed)
            metrics['final_rl_stats'] = rl_stats_list[-1]
        
        return metrics
    
    def _save_results(self, results: Dict, use_semantic: bool):
        """Save evaluation results to JSON."""
        suffix = 'semantic' if use_semantic else 'traditional'
        filename = f"evaluation_{suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"\n✓ Results saved to: {filepath}")
        
        return filepath
    
    async def compare_semantic_vs_traditional(self, max_pdfs: int = 5) -> Dict[str, Any]:
        """
        Compare semantic vs traditional chunking on the same PDFs.
        
        Args:
            max_pdfs: Number of PDFs to compare (for faster evaluation)
            
        Returns:
            Comparison results
        """
        logger.info("\n" + "=" * 70)
        logger.info("COMPARISON: SEMANTIC vs TRADITIONAL CHUNKING")
        logger.info("=" * 70)
        
        # Evaluate with semantic
        logger.info("\n1. Evaluating with SEMANTIC chunking...")
        semantic_results = await self.evaluate_all_pdfs(
            use_semantic=True,
            max_pdfs=max_pdfs
        )
        
        # Small delay
        await asyncio.sleep(2)
        
        # Evaluate with traditional
        logger.info("\n2. Evaluating with TRADITIONAL chunking...")
        traditional_results = await self.evaluate_all_pdfs(
            use_semantic=False,
            max_pdfs=max_pdfs
        )
        
        # Compare results
        comparison = self._create_comparison(semantic_results, traditional_results)
        
        # Save comparison
        comp_file = self.output_dir / f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(comp_file, 'w') as f:
            json.dump(comparison, f, indent=2, default=str)
        
        logger.info(f"\n✓ Comparison saved to: {comp_file}")
        
        # Print summary
        self._print_comparison_summary(comparison)
        
        return comparison
    
    def _create_comparison(
        self,
        semantic_results: Dict,
        traditional_results: Dict
    ) -> Dict[str, Any]:
        """Create comparison between semantic and traditional results."""
        sem_metrics = semantic_results['aggregate_metrics']
        trad_metrics = traditional_results['aggregate_metrics']
        
        return {
            'timestamp': datetime.now().isoformat(),
            'semantic': sem_metrics,
            'traditional': trad_metrics,
            'improvements': {
                'chunk_count_diff': sem_metrics['avg_chunks_per_pdf'] - trad_metrics['avg_chunks_per_pdf'],
                'chunk_count_pct': ((sem_metrics['avg_chunks_per_pdf'] / trad_metrics['avg_chunks_per_pdf']) - 1) * 100
                    if trad_metrics['avg_chunks_per_pdf'] > 0 else 0,
                'retrieval_score_diff': sem_metrics['avg_retrieval_score'] - trad_metrics['avg_retrieval_score'],
                'retrieval_improvement_pct': ((sem_metrics['avg_retrieval_score'] / trad_metrics['avg_retrieval_score']) - 1) * 100
                    if trad_metrics['avg_retrieval_score'] > 0 else 0,
                'consistency_improvement': ((trad_metrics['std_chunks_per_pdf'] - sem_metrics['std_chunks_per_pdf']) / trad_metrics['std_chunks_per_pdf']) * 100
                    if trad_metrics['std_chunks_per_pdf'] > 0 else 0,
            }
        }
    
    def _print_comparison_summary(self, comparison: Dict):
        """Print comparison summary."""
        logger.info("\n" + "=" * 70)
        logger.info("COMPARISON SUMMARY")
        logger.info("=" * 70)
        
        sem = comparison['semantic']
        trad = comparison['traditional']
        imp = comparison['improvements']
        
        logger.info(f"\nAverage Chunks per PDF:")
        logger.info(f"  Semantic:     {sem['avg_chunks_per_pdf']:.1f}")
        logger.info(f"  Traditional:  {trad['avg_chunks_per_pdf']:.1f}")
        logger.info(f"  Difference:   {imp['chunk_count_diff']:+.1f} ({imp['chunk_count_pct']:+.1f}%)")
        
        logger.info(f"\nAverage Retrieval Score:")
        logger.info(f"  Semantic:     {sem['avg_retrieval_score']:.3f}")
        logger.info(f"  Traditional:  {trad['avg_retrieval_score']:.3f}")
        logger.info(f"  Improvement:  {imp['retrieval_score_diff']:+.3f} ({imp['retrieval_improvement_pct']:+.1f}%)")
        
        logger.info(f"\nChunk Size Consistency:")
        logger.info(f"  Semantic std: {sem['std_chunks_per_pdf']:.2f}")
        logger.info(f"  Traditional std: {trad['std_chunks_per_pdf']:.2f}")
        logger.info(f"  Improvement:  {imp['consistency_improvement']:+.1f}%")
        
        logger.info("=" * 70)


async def main():
    """Run comprehensive evaluation."""
    # Check if we should use 5 PDFs (for comprehensive evaluation)
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--5pdf":
        output_dir = "./evaluation_results_5pdf"
        max_pdfs = 5
        logger.info("Running comprehensive 5-PDF evaluation")
    else:
        output_dir = "./evaluation_results"
        max_pdfs = 1
        logger.info("Running single-PDF quick test")
    
    evaluator = ComprehensiveEvaluator(output_dir=output_dir)
    
    # Compare semantic vs traditional
    results = await evaluator.compare_semantic_vs_traditional(max_pdfs=max_pdfs)
    
    logger.info("\n✅ Evaluation complete!")
    logger.info(f"Results saved to: {evaluator.output_dir}")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
