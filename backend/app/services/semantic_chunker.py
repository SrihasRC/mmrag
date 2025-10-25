"""
Semantic Chunker Module
=======================

Neural semantic boundary detection for intelligent document chunking.
Uses embedding-based similarity analysis to detect topic transitions
and create coherent chunks that preserve semantic flow.

Research Contribution: Structure-Aware Neural Chunking for Multimodal RAG
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

import nltk
from nltk.tokenize import sent_tokenize

logger = logging.getLogger(__name__)

# Download NLTK data on import (idempotent)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    logger.info("Downloading NLTK punkt tokenizer...")
    nltk.download('punkt', quiet=True)


@dataclass
class SemanticChunk:
    """Represents a semantically coherent chunk of text."""
    content: str
    sentences: List[str]
    start_idx: int
    end_idx: int
    coherence_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __len__(self):
        return len(self.content)
    
    def __str__(self):
        return f"SemanticChunk(sentences={len(self.sentences)}, chars={len(self.content)}, coherence={self.coherence_score:.3f})"


class AdaptiveThreshold:
    """
    RL-based adaptive threshold learning for semantic chunking.
    
    Learns optimal threshold values from retrieval feedback, adjusting
    chunking strategy based on downstream performance.
    
    This enables the system to improve over time by learning which
    chunking strategies lead to better retrieval quality.
    """
    
    def __init__(
        self,
        initial_multiplier: float = 0.5,
        learning_rate: float = 0.01,
        min_multiplier: float = 0.2,
        max_multiplier: float = 0.8
    ):
        """
        Initialize adaptive threshold learner.
        
        Args:
            initial_multiplier: Starting threshold multiplier
            learning_rate: How quickly to adapt (0.01 = 1% per update)
            min_multiplier: Minimum allowed multiplier
            max_multiplier: Maximum allowed multiplier
        """
        self.threshold_multiplier = initial_multiplier
        self.learning_rate = learning_rate
        self.min_multiplier = min_multiplier
        self.max_multiplier = max_multiplier
        
        # Track learning history
        self.feedback_history = []
        self.threshold_history = [initial_multiplier]
        self.total_updates = 0
        
        logger.info(
            f"AdaptiveThreshold initialized: "
            f"multiplier={initial_multiplier}, lr={learning_rate}"
        )
    
    def update_from_feedback(
        self,
        chunk_was_useful: bool,
        retrieval_score: float = 0.0
    ):
        """
        Update threshold based on retrieval feedback.
        
        Args:
            chunk_was_useful: Whether the chunk led to good retrieval
            retrieval_score: Optional relevance score (0-1)
        """
        # Record feedback
        self.feedback_history.append({
            'useful': chunk_was_useful,
            'score': retrieval_score,
            'threshold_before': self.threshold_multiplier
        })
        
        if chunk_was_useful and retrieval_score > 0.7:
            # Good retrieval - chunks are well-formed
            # Slight positive reinforcement
            self.threshold_multiplier += self.learning_rate * 0.5
        elif not chunk_was_useful or retrieval_score < 0.3:
            # Poor retrieval - may need different chunking
            # Adjust threshold to create different boundaries
            self.threshold_multiplier -= self.learning_rate
        
        # Clip to valid range
        self.threshold_multiplier = np.clip(
            self.threshold_multiplier,
            self.min_multiplier,
            self.max_multiplier
        )
        
        self.threshold_history.append(self.threshold_multiplier)
        self.total_updates += 1
        
        logger.debug(
            f"Threshold updated: {self.feedback_history[-1]['threshold_before']:.3f} → "
            f"{self.threshold_multiplier:.3f} (useful={chunk_was_useful}, "
            f"score={retrieval_score:.2f})"
        )
    
    def get_current_multiplier(self) -> float:
        """Get current threshold multiplier."""
        return self.threshold_multiplier
    
    def get_threshold(self, base_similarity: float, std_similarity: float) -> float:
        """
        Calculate adaptive threshold for boundary detection.
        
        Args:
            base_similarity: Mean similarity score
            std_similarity: Standard deviation of similarities
            
        Returns:
            Adaptive threshold value
        """
        return (base_similarity - (self.threshold_multiplier * std_similarity))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get learning statistics."""
        if not self.feedback_history:
            return {
                'total_updates': 0,
                'current_multiplier': self.threshold_multiplier
            }
        
        useful_count = sum(1 for f in self.feedback_history if f['useful'])
        avg_score = np.mean([f['score'] for f in self.feedback_history])
        
        return {
            'total_updates': self.total_updates,
            'current_multiplier': self.threshold_multiplier,
            'useful_rate': useful_count / len(self.feedback_history),
            'avg_retrieval_score': avg_score,
            'threshold_evolution': self.threshold_history[-10:],  # Last 10
            'multiplier_range': (
                min(self.threshold_history),
                max(self.threshold_history)
            )
        }


class SemanticChunker:
    """
    Neural semantic chunking using embedding-based boundary detection.
    
    This chunker analyzes semantic similarity between consecutive sentences
    to detect topic boundaries, creating chunks that preserve semantic coherence
    rather than using arbitrary character counts.
    
    Key Features:
    - Sentence-level embedding analysis
    - Dynamic threshold adaptation
    - Document type awareness
    - Min/max size constraints
    - Coherence scoring
    """
    
    # Document type threshold multipliers
    TYPE_MULTIPLIERS = {
        'resume': 0.4,         # More aggressive splits for structured content
        'short_document': 0.4,
        'academic_paper': 0.6, # Moderate splits for academic content
        'technical_doc': 0.55,
        'general': 0.5
    }
    
    def __init__(
        self,
        embeddings_service,
        min_sentences: int = 3,
        max_sentences: int = 30,
        base_threshold: float = 0.5,
        batch_size: int = 96,
        use_adaptive_threshold: bool = True
    ):
        """
        Initialize the semantic chunker.
        
        Args:
            embeddings_service: Cohere embeddings service (CohereEmbeddings instance)
            min_sentences: Minimum sentences per chunk
            max_sentences: Maximum sentences per chunk
            base_threshold: Base similarity threshold (adjusted per document type)
            batch_size: Batch size for embedding API calls (Cohere limit: 96)
            use_adaptive_threshold: Enable RL-based adaptive thresholding
        """
        self.embeddings = embeddings_service
        self.min_sentences = min_sentences
        self.max_sentences = max_sentences
        self.base_threshold = base_threshold
        self.batch_size = batch_size
        
        # Initialize adaptive threshold (RL component)
        self.adaptive_threshold = None
        if use_adaptive_threshold:
            self.adaptive_threshold = AdaptiveThreshold(
                initial_multiplier=base_threshold,
                learning_rate=0.01
            )
        
        logger.info(
            f"SemanticChunker initialized: "
            f"min_sentences={min_sentences}, max_sentences={max_sentences}, "
            f"base_threshold={base_threshold}, adaptive={use_adaptive_threshold}"
        )
    
    def chunk_document(
        self,
        text: str,
        doc_type: str = 'general'
    ) -> List[SemanticChunk]:
        """
        Chunk a document using semantic boundary detection.
        
        Args:
            text: The text to chunk
            doc_type: Document type for adaptive thresholding
            
        Returns:
            List of SemanticChunk objects
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to chunk_document")
            return []
        
        try:
            # Step 1: Split into sentences
            sentences = self._split_into_sentences(text)
            if len(sentences) == 0:
                logger.warning("No sentences found in text")
                return []
            
            logger.info(f"Split text into {len(sentences)} sentences")
            
            # If very few sentences, return as single chunk
            if len(sentences) <= self.min_sentences:
                return [self._create_single_chunk(sentences, 0, len(sentences))]
            
            # Step 2: Embed sentences
            embeddings = self._embed_sentences(sentences)
            
            # Step 3: Compute similarities
            similarities = self._compute_similarities(embeddings)
            
            # Step 4: Detect boundaries
            boundaries = self._detect_boundaries(similarities, sentences, doc_type)
            
            # Step 5: Create chunks
            chunks = self._create_chunks(sentences, boundaries, similarities)
            
            logger.info(
                f"Created {len(chunks)} semantic chunks "
                f"(avg coherence: {np.mean([c.coherence_score for c in chunks]):.3f})"
            )
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error in semantic chunking: {str(e)}", exc_info=True)
            # Return simple fallback
            return self._fallback_chunking(text)
    
    def provide_feedback(
        self,
        chunk_was_useful: bool,
        retrieval_score: float = 0.0
    ):
        """
        Provide feedback to adaptive threshold for RL learning.
        
        Args:
            chunk_was_useful: Whether the chunk led to successful retrieval
            retrieval_score: Relevance score of retrieved content (0-1)
        """
        if self.adaptive_threshold:
            self.adaptive_threshold.update_from_feedback(
                chunk_was_useful,
                retrieval_score
            )
            logger.debug(
                f"Feedback provided: useful={chunk_was_useful}, score={retrieval_score:.2f}"
            )
    
    def get_adaptive_stats(self) -> Dict[str, Any]:
        """Get statistics from adaptive threshold learning."""
        if self.adaptive_threshold:
            return self.adaptive_threshold.get_statistics()
        return {}
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using NLTK.
        
        Args:
            text: Input text
            
        Returns:
            List of sentences (filtered for minimum length)
        """
        try:
            # Use NLTK's sentence tokenizer
            sentences = sent_tokenize(text)
            
            # Filter out very short sentences (likely noise)
            filtered = [s.strip() for s in sentences if len(s.strip()) > 10]
            
            return filtered
            
        except Exception as e:
            logger.error(f"Error splitting sentences: {str(e)}")
            # Fallback: simple split on periods
            return [s.strip() + '.' for s in text.split('.') if len(s.strip()) > 10]
    
    def _embed_sentences(self, sentences: List[str], use_sliding_window: bool = True) -> np.ndarray:
        """
        Embed sentences using Cohere embeddings with batching.
        
        Optionally uses sliding window context for richer representations.
        
        Args:
            sentences: List of sentences to embed
            use_sliding_window: Whether to use 3-sentence windows (better context)
            
        Returns:
            NumPy array of embeddings (shape: [num_sentences, embedding_dim])
        """
        embeddings_list = []
        
        try:
            # Prepare input texts (with or without sliding windows)
            if use_sliding_window and len(sentences) > 1:
                input_texts = []
                for i in range(len(sentences)):
                    # Create 3-sentence window centered on current sentence
                    start_idx = max(0, i - 1)
                    end_idx = min(len(sentences), i + 2)
                    window = sentences[start_idx:end_idx]
                    # Join with space to create context-aware representation
                    input_texts.append(' '.join(window))
                
                logger.debug(f"Using sliding windows: {len(input_texts)} windows created")
            else:
                input_texts = sentences
            
            # Process in batches to respect API limits
            for i in range(0, len(input_texts), self.batch_size):
                batch = input_texts[i:i + self.batch_size]
                
                # Call Cohere embeddings
                batch_embeddings = self.embeddings.embed_documents(batch)
                embeddings_list.extend(batch_embeddings)
                
                logger.debug(f"Embedded batch {i//self.batch_size + 1}/{(len(input_texts)-1)//self.batch_size + 1}")
            
            return np.array(embeddings_list)
            
        except Exception as e:
            logger.error(f"Error embedding sentences: {str(e)}")
            raise
    
    def _compute_similarities(self, embeddings: np.ndarray) -> List[float]:
        """
        Compute cosine similarity between consecutive sentence embeddings.
        
        Args:
            embeddings: Array of sentence embeddings
            
        Returns:
            List of similarity scores between consecutive sentences
        """
        similarities = []
        
        for i in range(len(embeddings) - 1):
            # Compute cosine similarity between consecutive sentences
            sim = cosine_similarity(
                embeddings[i].reshape(1, -1),
                embeddings[i + 1].reshape(1, -1)
            )[0][0]
            similarities.append(float(sim))
        
        return similarities
    
    def _detect_boundaries(
        self,
        similarities: List[float],
        sentences: List[str],
        doc_type: str
    ) -> List[int]:
        """
        Detect chunk boundaries based on similarity drops.
        
        Uses dynamic thresholding based on similarity distribution
        and document type awareness.
        
        Args:
            similarities: List of similarity scores
            sentences: Original sentences
            doc_type: Document type for adaptive thresholding
            
        Returns:
            List of boundary indices (sentence indices)
        """
        if len(similarities) == 0:
            return [0, len(sentences)]
        
        # Calculate dynamic threshold
        mean_sim = np.mean(similarities)
        std_sim = np.std(similarities)
        
        # Use adaptive threshold if available (RL-enhanced)
        if self.adaptive_threshold:
            threshold = self.adaptive_threshold.get_threshold(mean_sim, std_sim)
            logger.debug(
                f"Using adaptive threshold: multiplier={self.adaptive_threshold.get_current_multiplier():.3f}"
            )
        else:
            threshold = mean_sim - (self.base_threshold * std_sim)
            # Apply document type multiplier
            type_multiplier = self.TYPE_MULTIPLIERS.get(doc_type.lower(), 0.5)
            threshold *= type_multiplier
        
        logger.debug(
            f"Boundary detection: mean_sim={mean_sim:.3f}, std_sim={std_sim:.3f}, "
            f"threshold={threshold:.3f}, doc_type={doc_type}"
        )
        
        boundaries = [0]  # Always start at 0
        current_chunk_size = 0
        
        for i, sim in enumerate(similarities):
            current_chunk_size += 1
            
            # Create boundary if:
            # 1. Similarity drops below threshold
            # 2. Current chunk has minimum size
            # 3. Not creating too many boundaries
            if (sim < threshold and 
                current_chunk_size >= self.min_sentences):
                boundaries.append(i + 1)
                current_chunk_size = 0
                logger.debug(f"Boundary at sentence {i+1} (sim={sim:.3f} < {threshold:.3f})")
            
            # Force boundary at maximum size
            elif current_chunk_size >= self.max_sentences:
                boundaries.append(i + 1)
                current_chunk_size = 0
                logger.debug(f"Max size boundary at sentence {i+1}")
        
        # Add final boundary
        if boundaries[-1] != len(sentences):
            boundaries.append(len(sentences))
        
        return boundaries
    
    def _create_chunks(
        self,
        sentences: List[str],
        boundaries: List[int],
        similarities: List[float]
    ) -> List[SemanticChunk]:
        """
        Create SemanticChunk objects from sentences and boundaries.
        
        Args:
            sentences: List of sentences
            boundaries: Boundary indices
            similarities: Similarity scores
            
        Returns:
            List of SemanticChunk objects
        """
        chunks = []
        
        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]
            
            chunk_sentences = sentences[start:end]
            chunk_content = ' '.join(chunk_sentences)
            
            # Calculate chunk coherence (average similarity within chunk)
            if end - start > 1 and start < len(similarities):
                chunk_sims = similarities[start:min(end-1, len(similarities))]
                coherence = float(np.mean(chunk_sims)) if chunk_sims else 1.0
            else:
                coherence = 1.0  # Single sentence = perfect coherence
            
            chunk = SemanticChunk(
                content=chunk_content,
                sentences=chunk_sentences,
                start_idx=start,
                end_idx=end,
                coherence_score=coherence,
                metadata={
                    'num_sentences': len(chunk_sentences),
                    'char_count': len(chunk_content),
                    'word_count': len(chunk_content.split())
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_single_chunk(
        self,
        sentences: List[str],
        start: int,
        end: int
    ) -> SemanticChunk:
        """Create a single chunk (for short documents)."""
        return SemanticChunk(
            content=' '.join(sentences),
            sentences=sentences,
            start_idx=start,
            end_idx=end,
            coherence_score=1.0,
            metadata={
                'num_sentences': len(sentences),
                'char_count': len(' '.join(sentences)),
                'word_count': len(' '.join(sentences).split())
            }
        )
    
    def _fallback_chunking(self, text: str) -> List[SemanticChunk]:
        """
        Fallback chunking method if semantic chunking fails.
        
        Simple character-based chunking with 1000-char chunks.
        """
        logger.warning("Using fallback chunking method")
        
        chunks = []
        chunk_size = 1000
        
        for i in range(0, len(text), chunk_size):
            chunk_text = text[i:i + chunk_size]
            chunks.append(
                SemanticChunk(
                    content=chunk_text,
                    sentences=[chunk_text],
                    start_idx=i,
                    end_idx=i + len(chunk_text),
                    coherence_score=0.0,
                    metadata={
                        'num_sentences': 1,
                        'char_count': len(chunk_text),
                        'word_count': len(chunk_text.split()),
                        'fallback': True
                    }
                )
            )
        
        return chunks


# Utility functions for analysis
def analyze_chunks(chunks: List[SemanticChunk]) -> Dict[str, Any]:
    """
    Analyze a list of chunks and return statistics.
    
    Args:
        chunks: List of SemanticChunk objects
        
    Returns:
        Dictionary of statistics
    """
    if not chunks:
        return {}
    
    return {
        'num_chunks': len(chunks),
        'avg_coherence': float(np.mean([c.coherence_score for c in chunks])),
        'min_coherence': float(np.min([c.coherence_score for c in chunks])),
        'max_coherence': float(np.max([c.coherence_score for c in chunks])),
        'avg_sentences': float(np.mean([c.metadata['num_sentences'] for c in chunks])),
        'avg_chars': float(np.mean([c.metadata['char_count'] for c in chunks])),
        'total_chars': sum(c.metadata['char_count'] for c in chunks),
        'sentence_distribution': [c.metadata['num_sentences'] for c in chunks]
    }
