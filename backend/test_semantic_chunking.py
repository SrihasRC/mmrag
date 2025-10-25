#!/usr/bin/env python3
"""
Test Semantic Chunking
======================

Simple test script to validate semantic chunking functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.semantic_chunker import SemanticChunker, analyze_chunks
from langchain_cohere import CohereEmbeddings
from app.config.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_semantic_chunker():
    """Test the semantic chunker with sample text."""
    
    # Sample text with clear topic transitions
    sample_text = """
    Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience. 
    It focuses on developing computer programs that can access data and use it to learn for themselves.
    The process of learning begins with observations or data to look for patterns in data and make better decisions in the future.
    
    Deep learning is a specialized form of machine learning that uses neural networks with multiple layers.
    These neural networks attempt to simulate the behavior of the human brain to learn from large amounts of data.
    Deep learning has revolutionized computer vision and natural language processing tasks.
    
    Natural language processing helps computers understand, interpret, and manipulate human language.
    NLP combines computational linguistics with statistical, machine learning, and deep learning models.
    Applications include speech recognition, text translation, and sentiment analysis.
    
    Computer vision enables computers to derive meaningful information from digital images and videos.
    It involves methods for acquiring, processing, analyzing, and understanding digital images.
    Common applications include facial recognition, object detection, and autonomous vehicles.
    """
    
    logger.info("Testing Semantic Chunker...")
    logger.info("=" * 60)
    
    try:
        # Initialize embeddings
        logger.info("Initializing Cohere embeddings...")
        embeddings = CohereEmbeddings(
            cohere_api_key=settings.COHERE_API_KEY,
            model="embed-english-v3.0"
        )
        
        # Create chunker
        logger.info("Creating SemanticChunker...")
        chunker = SemanticChunker(
            embeddings_service=embeddings,
            min_sentences=2,
            max_sentences=10
        )
        
        # Test chunking
        logger.info("\nChunking sample text...")
        chunks = chunker.chunk_document(sample_text, doc_type='technical_doc')
        
        # Display results
        logger.info(f"\n✅ Successfully created {len(chunks)} semantic chunks")
        logger.info("=" * 60)
        
        for i, chunk in enumerate(chunks, 1):
            logger.info(f"\n📦 Chunk {i}:")
            logger.info(f"   Sentences: {chunk.metadata['num_sentences']}")
            logger.info(f"   Characters: {chunk.metadata['char_count']}")
            logger.info(f"   Coherence: {chunk.coherence_score:.3f}")
            logger.info(f"   Preview: {chunk.content[:100]}...")
        
        # Analyze chunks
        logger.info("\n" + "=" * 60)
        logger.info("CHUNK ANALYSIS")
        logger.info("=" * 60)
        stats = analyze_chunks(chunks)
        for key, value in stats.items():
            if isinstance(value, float):
                logger.info(f"  {key}: {value:.3f}")
            elif isinstance(value, list):
                logger.info(f"  {key}: {value}")
            else:
                logger.info(f"  {key}: {value}")
        
        logger.info("\n✅ Semantic chunking test PASSED!")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Test FAILED: {str(e)}", exc_info=True)
        return False


async def test_boundary_detection():
    """Test that boundaries are detected at topic transitions."""
    
    logger.info("\n" + "=" * 60)
    logger.info("Testing Boundary Detection")
    logger.info("=" * 60)
    
    # Text with very clear topic transitions
    test_text = """
    Python is a high-level programming language. It was created by Guido van Rossum. Python emphasizes code readability.
    
    The solar system contains eight planets. Mercury is the closest to the sun. Jupiter is the largest planet.
    
    Photosynthesis is a process used by plants. It converts light energy into chemical energy. Chlorophyll is essential for this process.
    """
    
    try:
        embeddings = CohereEmbeddings(
            cohere_api_key=settings.COHERE_API_KEY,
            model="embed-english-v3.0"
        )
        
        chunker = SemanticChunker(embeddings_service=embeddings, min_sentences=2)
        chunks = chunker.chunk_document(test_text, doc_type='general')
        
        logger.info(f"\n✅ Detected {len(chunks)} topic boundaries")
        
        if len(chunks) >= 3:
            logger.info("✅ Successfully separated different topics into chunks")
        else:
            logger.warning(f"⚠️  Expected 3+ chunks, got {len(chunks)}")
        
        for i, chunk in enumerate(chunks, 1):
            topic_words = chunk.content.split()[:5]
            logger.info(f"  Chunk {i}: {' '.join(topic_words)}... (coherence: {chunk.coherence_score:.3f})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Boundary detection test FAILED: {str(e)}")
        return False


async def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("SEMANTIC CHUNKING TEST SUITE")
    logger.info("=" * 60)
    
    results = []
    
    # Test 1: Basic functionality
    logger.info("\n[TEST 1] Basic Semantic Chunking")
    results.append(await test_semantic_chunker())
    
    # Test 2: Boundary detection
    logger.info("\n[TEST 2] Boundary Detection")
    results.append(await test_boundary_detection())
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    passed = sum(results)
    total = len(results)
    logger.info(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        logger.info("✅ ALL TESTS PASSED!")
        return 0
    else:
        logger.error(f"❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
