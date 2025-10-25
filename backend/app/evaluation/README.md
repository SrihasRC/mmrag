# Testing Neural Semantic Chunking

This directory contains tests and evaluation tools for the semantic chunking feature.

## Quick Test

Run the basic test to verify semantic chunking is working:

```bash
cd backend
python test_semantic_chunking.py
```

This will:
- ✅ Test basic semantic chunking functionality
- ✅ Verify boundary detection at topic transitions
- ✅ Show coherence scores and statistics

## Expected Output

```
SEMANTIC CHUNKING TEST SUITE
============================================================

[TEST 1] Basic Semantic Chunking
Creating SemanticChunker...
Chunking sample text...
✅ Successfully created 4 semantic chunks

📦 Chunk 1:
   Sentences: 3
   Characters: 267
   Coherence: 0.842
   Preview: Machine learning is a subset...

[TEST 2] Boundary Detection
✅ Detected 3 topic boundaries
✅ Successfully separated different topics into chunks

TEST SUMMARY
Tests Passed: 2/2
✅ ALL TESTS PASSED!
```

## Evaluation Tools

### Compare Chunking Methods

```python
from app.evaluation.chunking_comparison import ChunkingComparator

comparator = ChunkingComparator()

# Process with both methods
semantic_result = process_with_semantic(pdf_path)
traditional_result = process_with_traditional(pdf_path)

# Compare
comparison = comparator.compare_single_document(
    pdf_path,
    semantic_result,
    traditional_result
)

# Generate report
print(comparator.generate_report())
```

## Testing with Real PDFs

### Via API

```bash
# With semantic chunking (default)
curl -X POST "http://localhost:8000/api/v1/rag/upload?use_semantic_chunking=true" \
  -F "file=@your_document.pdf"

# With traditional chunking (for comparison)
curl -X POST "http://localhost:8000/api/v1/rag/upload?use_semantic_chunking=false" \
  -F "file=@your_document.pdf"
```

### Check Processing Logs

Look for these log messages:
- `SemanticChunker initialized successfully`
- `Using semantic chunking for: filename.pdf`
- `Semantic chunking created N chunks (avg coherence: 0.XXX)`

## Key Metrics to Monitor

1. **Number of Chunks**: Semantic may create more or fewer chunks than traditional
2. **Coherence Score**: 0.7-0.9 is good (high coherence within chunks)
3. **Chunk Size Distribution**: Should be more consistent with semantic chunking
4. **Retrieval Quality**: Better answers from semantically coherent chunks

## Troubleshooting

### If semantic chunking is not being used:

1. Check logs for: `Could not initialize SemanticChunker`
2. Verify Cohere API key is set in `.env`
3. Ensure scikit-learn is installed: `pip install scikit-learn`
4. Check NLTK data: `python -c "import nltk; nltk.download('punkt')"`

### If getting poor coherence scores:

- Try adjusting `base_threshold` in SemanticChunker initialization
- Check if document type is detected correctly
- Some documents may naturally have lower coherence (mixed topics)

## Performance Notes

- **Embedding time**: ~2-3 seconds per 100 sentences (Cohere API)
- **Batch processing**: 96 sentences per API call
- **Memory usage**: Minimal (embeddings computed in batches)
- **Fallback**: Automatic fallback to traditional chunking on errors
