#!/usr/bin/env python3
"""
Quick verification script to analyze retrieval quality from evaluation results.
Shows score distributions and examples to verify similarity scores make sense.
"""

import json
from pathlib import Path


def analyze_results():
    """Analyze evaluation results to verify retrieval quality."""
    
    results_dir = Path("evaluation_results_5pdf")
    
    # Load semantic results
    semantic_files = list(results_dir.glob("evaluation_semantic_*.json"))
    traditional_files = list(results_dir.glob("evaluation_traditional_*.json"))
    
    if not semantic_files or not traditional_files:
        print("❌ Evaluation results not found. Run evaluation first.")
        return
    
    semantic_path = sorted(semantic_files)[-1]  # Latest
    traditional_path = sorted(traditional_files)[-1]
    
    print("=" * 80)
    print("RETRIEVAL QUALITY VERIFICATION")
    print("=" * 80)
    
    with open(semantic_path) as f:
        semantic_data = json.load(f)
    
    with open(traditional_path) as f:
        traditional_data = json.load(f)
    
    # Analyze semantic chunking results
    print("\n📊 SEMANTIC CHUNKING")
    print("-" * 80)
    
    all_semantic_scores = []
    for pdf_result in semantic_data['pdf_results']:
        print(f"\n{pdf_result['pdf_name']}:")
        print(f"  Chunks: {pdf_result['num_chunks']}")
        print(f"  Avg score: {pdf_result['avg_retrieval_score']:.4f}")
        
        for query in pdf_result['query_details']:
            all_semantic_scores.append(query['score'])
            print(f"    {query['query_type']}: {query['score']:.4f} ({query['docs_retrieved']} docs)")
    
    # Analyze traditional chunking results
    print("\n\n📊 TRADITIONAL CHUNKING")
    print("-" * 80)
    
    all_traditional_scores = []
    for pdf_result in traditional_data['pdf_results']:
        print(f"\n{pdf_result['pdf_name']}:")
        print(f"  Chunks: {pdf_result['num_chunks']}")
        print(f"  Avg score: {pdf_result['avg_retrieval_score']:.4f}")
        
        for query in pdf_result['query_details']:
            all_traditional_scores.append(query['score'])
            print(f"    {query['query_type']}: {query['score']:.4f} ({query['docs_retrieved']} docs)")
    
    # Statistical summary
    print("\n\n" + "=" * 80)
    print("STATISTICAL ANALYSIS")
    print("=" * 80)
    
    import statistics
    
    sem_mean = statistics.mean(all_semantic_scores)
    sem_median = statistics.median(all_semantic_scores)
    sem_stdev = statistics.stdev(all_semantic_scores) if len(all_semantic_scores) > 1 else 0
    sem_min = min(all_semantic_scores)
    sem_max = max(all_semantic_scores)
    
    trad_mean = statistics.mean(all_traditional_scores)
    trad_median = statistics.median(all_traditional_scores)
    trad_stdev = statistics.stdev(all_traditional_scores) if len(all_traditional_scores) > 1 else 0
    trad_min = min(all_traditional_scores)
    trad_max = max(all_traditional_scores)
    
    print("\nSemantic Chunking:")
    print(f"  Mean:   {sem_mean:.4f}")
    print(f"  Median: {sem_median:.4f}")
    print(f"  Std:    {sem_stdev:.4f}")
    print(f"  Range:  [{sem_min:.4f}, {sem_max:.4f}]")
    
    print("\nTraditional Chunking:")
    print(f"  Mean:   {trad_mean:.4f}")
    print(f"  Median: {trad_median:.4f}")
    print(f"  Std:    {trad_stdev:.4f}")
    print(f"  Range:  [{trad_min:.4f}, {trad_max:.4f}]")
    
    print("\nComparison:")
    diff = sem_mean - trad_mean
    pct_diff = (diff / trad_mean) * 100
    print(f"  Difference: {diff:+.4f} ({pct_diff:+.2f}%)")
    
    # Interpretation
    print("\n\n" + "=" * 80)
    print("INTERPRETATION")
    print("=" * 80)
    
    print("\n📏 Score Range Check:")
    if 0 <= sem_min and sem_max <= 1:
        print("  ✅ Semantic scores in valid range [0, 1]")
    else:
        print(f"  ❌ Semantic scores outside range: [{sem_min:.4f}, {sem_max:.4f}]")
    
    if 0 <= trad_min and trad_max <= 1:
        print("  ✅ Traditional scores in valid range [0, 1]")
    else:
        print(f"  ❌ Traditional scores outside range: [{trad_min:.4f}, {trad_max:.4f}]")
    
    print("\n🎯 Retrieval Quality:")
    if sem_mean > 0.5:
        print(f"  ✅ HIGH quality (avg {sem_mean:.3f})")
        print("     Semantic: Retrieved chunks are highly relevant")
    elif sem_mean > 0.4:
        print(f"  ⚠️  MODERATE quality (avg {sem_mean:.3f})")
        print("     Semantic: Retrieved chunks are somewhat relevant")
    else:
        print(f"  ❌ LOW quality (avg {sem_mean:.3f})")
        print("     Semantic: Retrieved chunks may not be very relevant")
    
    if trad_mean > 0.5:
        print(f"  ✅ HIGH quality (avg {trad_mean:.3f})")
        print("     Traditional: Retrieved chunks are highly relevant")
    elif trad_mean > 0.4:
        print(f"  ⚠️  MODERATE quality (avg {trad_mean:.3f})")
        print("     Traditional: Retrieved chunks are somewhat relevant")
    else:
        print(f"  ❌ LOW quality (avg {trad_mean:.3f})")
        print("     Traditional: Retrieved chunks may not be very relevant")
    
    print("\n🏆 Winner:")
    if pct_diff > 5:
        print(f"  ✅ Semantic chunking is {pct_diff:.1f}% BETTER")
        print("     → Semantic chunking produces more relevant chunks!")
    elif pct_diff > 0:
        print(f"  ✅ Semantic chunking is slightly better (+{pct_diff:.1f}%)")
        print("     → Marginal improvement, but in right direction")
    elif pct_diff > -5:
        print(f"  ⚠️  Semantic chunking is slightly worse ({pct_diff:.1f}%)")
        print("     → Very close, could improve with tuning")
    else:
        print(f"  ❌ Semantic chunking is {abs(pct_diff):.1f}% WORSE")
        print("     → Need to investigate why semantic is underperforming")
    
    print("\n💡 Notes on Scores:")
    print("  • Cosine similarity range: [0, 1]")
    print("  • 0 = completely unrelated")
    print("  • 1 = identical")
    print("  • >0.7 = very similar")
    print("  • 0.4-0.7 = moderately similar")
    print("  • <0.4 = not very similar")
    print("\n  Current scores (0.41-0.47) suggest:")
    print("  → Retrieved chunks are moderately related to queries")
    print("  → Not perfect matches, but relevant content")
    print("  → Room for improvement, but reasonable baseline")


if __name__ == "__main__":
    analyze_results()
