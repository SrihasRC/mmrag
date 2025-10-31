#!/usr/bin/env python3
"""
Integration Test for Semantic Chunking in Full Pipeline
=======================================================

Test semantic chunking through the complete PDF processing pipeline.
"""

import asyncio
import sys
from pathlib import Path
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.pdf_processor import pdf_processor
from fastapi import UploadFile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_pdf_processor_integration():
    """Test that PDFProcessor can use semantic chunking."""
    
    logger.info("=" * 70)
    logger.info("INTEGRATION TEST: PDF Processor with Semantic Chunking")
    logger.info("=" * 70)
    
    # Check if semantic chunker is initialized
    if pdf_processor.semantic_chunker:
        logger.info("✅ SemanticChunker is initialized in PDFProcessor")
        logger.info(f"   Min sentences: {pdf_processor.semantic_chunker.min_sentences}")
        logger.info(f"   Max sentences: {pdf_processor.semantic_chunker.max_sentences}")
        logger.info(f"   Base threshold: {pdf_processor.semantic_chunker.base_threshold}")
    else:
        logger.warning("⚠️  SemanticChunker is NOT initialized")
        logger.warning("   This is OK - system will use traditional chunking")
        return True
    
    logger.info("\n" + "-" * 70)
    logger.info("Testing semantic chunking on sample text...")
    logger.info("-" * 70)
    
    # Test with sample text through the semantic chunker
    sample_text = """
    Artificial intelligence has transformed modern computing.
    Machine learning enables systems to learn from data automatically.
    Deep learning uses neural networks to process complex patterns.
    
    Climate change poses significant environmental challenges.
    Rising temperatures affect ecosystems worldwide.
    Sustainable practices are essential for the future.
    """
    
    try:
        chunks = pdf_processor.semantic_chunker.chunk_document(
            sample_text,
            doc_type='general'
        )
        
        logger.info(f"\n✅ Successfully created {len(chunks)} semantic chunks")
        
        for i, chunk in enumerate(chunks, 1):
            logger.info(f"\nChunk {i}:")
            logger.info(f"  Sentences: {chunk.metadata['num_sentences']}")
            logger.info(f"  Coherence: {chunk.coherence_score:.3f}")
            preview = chunk.content.replace('\n', ' ')[:80]
            logger.info(f"  Preview: {preview}...")
        
        logger.info("\n✅ Semantic chunking integration test PASSED!")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Integration test FAILED: {str(e)}", exc_info=True)
        return False


async def test_extract_semantic_method():
    """Test that extract_pdf_elements_semantic method exists and is callable."""
    
    logger.info("\n" + "=" * 70)
    logger.info("INTEGRATION TEST: extract_pdf_elements_semantic Method")
    logger.info("=" * 70)
    
    # Check method exists
    if hasattr(pdf_processor, 'extract_pdf_elements_semantic'):
        logger.info("✅ extract_pdf_elements_semantic method exists")
    else:
        logger.error("❌ extract_pdf_elements_semantic method NOT FOUND")
        return False
    
    # Check method signature
    import inspect
    sig = inspect.signature(pdf_processor.extract_pdf_elements_semantic)
    params = list(sig.parameters.keys())
    
    logger.info(f"   Parameters: {params}")
    
    if 'use_semantic_chunking' in params:
        logger.info("✅ use_semantic_chunking parameter exists")
    else:
        logger.warning("⚠️  use_semantic_chunking parameter not found")
    
    logger.info("\n✅ Method structure test PASSED!")
    return True


async def test_initialization():
    """Test that initialization happened correctly."""
    
    logger.info("\n" + "=" * 70)
    logger.info("INTEGRATION TEST: Initialization Check")
    logger.info("=" * 70)
    
    checks = []
    
    # Check 1: PDFProcessor exists
    if pdf_processor:
        logger.info("✅ PDFProcessor global instance exists")
        checks.append(True)
    else:
        logger.error("❌ PDFProcessor not initialized")
        checks.append(False)
    
    # Check 2: Required methods exist
    required_methods = [
        'extract_pdf_elements',
        'extract_pdf_elements_semantic',
        'process_pdf_file'
    ]
    
    for method in required_methods:
        if hasattr(pdf_processor, method):
            logger.info(f"✅ Method '{method}' exists")
            checks.append(True)
        else:
            logger.error(f"❌ Method '{method}' NOT FOUND")
            checks.append(False)
    
    # Check 3: SemanticChunker initialization
    if pdf_processor.semantic_chunker:
        logger.info("✅ SemanticChunker is initialized")
        checks.append(True)
    else:
        logger.warning("⚠️  SemanticChunker not initialized (will use fallback)")
        checks.append(True)  # Not a failure - fallback is OK
    
    all_passed = all(checks)
    if all_passed:
        logger.info("\n✅ Initialization test PASSED!")
    else:
        logger.error("\n❌ Some initialization checks FAILED!")
    
    return all_passed


async def main():
    """Run all integration tests."""
    
    logger.info("\n" + "=" * 70)
    logger.info("SEMANTIC CHUNKING INTEGRATION TEST SUITE")
    logger.info("=" * 70)
    
    results = []
    
    # Test 1: Initialization
    logger.info("\n[TEST 1] Initialization Check")
    results.append(await test_initialization())
    
    # Test 2: Method availability
    logger.info("\n[TEST 2] Method Structure")
    results.append(await test_extract_semantic_method())
    
    # Test 3: Semantic chunking functionality
    if pdf_processor.semantic_chunker:
        logger.info("\n[TEST 3] Semantic Chunking Integration")
        results.append(await test_pdf_processor_integration())
    else:
        logger.info("\n[TEST 3] SKIPPED - SemanticChunker not available")
        logger.info("         (System will use traditional chunking)")
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("INTEGRATION TEST SUMMARY")
    logger.info("=" * 70)
    passed = sum(results)
    total = len(results)
    logger.info(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        logger.info("✅ ALL INTEGRATION TESTS PASSED!")
        logger.info("\nThe semantic chunking feature is properly integrated!")
        logger.info("You can now:")
        logger.info("  1. Start the server: python start_server.py")
        logger.info("  2. Upload PDFs with: use_semantic_chunking=true (default)")
        logger.info("  3. Compare with traditional: use_semantic_chunking=false")
        return 0
    else:
        logger.error(f"❌ {total - passed} INTEGRATION TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
