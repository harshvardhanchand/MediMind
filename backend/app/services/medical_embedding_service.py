"""
Medical Embedding Service 
Handles creation and similarity search of medical situation embeddings
"""

import numpy as np
import json
import hashlib
import logging
import threading
from collections import OrderedDict
from typing import Dict, List, Any, Tuple, Optional
import torch
from transformers import AutoTokenizer, AutoModel


logger = logging.getLogger(__name__)

class MedicalEmbeddingService:
    """
    Medical embedding service using BioBERT for medical-specific understanding
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.model_name = 'microsoft/PubMedBERT-base-uncased-abstract-fulltext'
        self.embedding_dim = 768  # PubMedBERT dimension
        self.similarity_threshold = similarity_threshold
        
        # Thread-safe LRU cache for embeddings with proper tracking
        self._cache_lock = threading.Lock()
        self._embedding_cache = OrderedDict()  # True LRU cache using OrderedDict
        self._cache_max_size = 1000
        
        # Cache statistics tracking
        self._cache_hits = 0
        self._cache_requests = 0
        
        # Initialize PubMedBERT
        self._init_pubmedbert()
        
        # Initialize medical NER (optional - for entity extraction)
        self._init_medical_ner()
    
    def _init_pubmedbert(self):
        """Initialize PubMedBERT model and tokenizer"""
        try:
            logger.info("Loading PubMedBERT model for medical embeddings...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.eval()  # Set to evaluation mode
            
            # Use GPU if available
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.model.to(self.device)
            
            # Set flag to indicate PubMedBERT is loaded successfully
            self.use_pubmedbert = True
            
            logger.info(f"PubMedBERT loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load PubMedBERT: {str(e)}")
            # Store the error for potential use in final error message
            self._pubmedbert_error = str(e)
            # Fallback to BioBERT-large if PubMedBERT fails
            self._init_fallback_model()
    
    def _init_fallback_model(self):
        """Fallback to BioBERT-large if PubMedBERT fails"""
        try:
            logger.info("Loading BioBERT-large as fallback model...")
            # Use BioBERT-large - medical domain BERT model
            self.tokenizer = AutoTokenizer.from_pretrained('dmis-lab/biobert-large-cased-v1.1')
            self.model = AutoModel.from_pretrained('dmis-lab/biobert-large-cased-v1.1')
            self.model.eval()
            
            # Use GPU if available
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.model.to(self.device)
            
            self.embedding_dim = 1024  # BERT-large dimension
            self.use_pubmedbert = False
            logger.info(f"BioBERT-large fallback loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load BioBERT fallback: {str(e)}")
            # If both models fail, raise exception - no third fallback
            pubmedbert_err = getattr(self, '_pubmedbert_error', 'Unknown')
            raise RuntimeError(
                f"Failed to load both PubMedBERT and BioBERT-large models. "
                f"PubMedBERT error: {pubmedbert_err}. "
                f"BioBERT error: {str(e)}"
            )
    
    def _init_medical_ner(self):
        """Initialize medical NER for entity extraction using spaCy medical models"""
        try:
            import spacy
            # Try to load a medical NER model (requires separate installation)
            try:
                self.nlp = spacy.load("en_core_sci_md")  # scispaCy medical model
                logger.info("Medical NER initialized with scispaCy")
            except OSError:
                # Fallback to general English model
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("Medical NER initialized with general English model")
        except Exception as e:
            logger.warning(f"Medical NER not available: {str(e)}")
            self.nlp = None
    
    def create_medical_embedding(self, medical_profile: Dict[str, Any]) -> np.ndarray:
        """
        Create embedding vector from medical profile using PubMedBERT with caching
        """
        try:
            # Convert medical profile to text
            medical_text = self._medical_profile_to_text(medical_profile)
            
            # Thread-safe cache operations
            with self._cache_lock:
                self._cache_requests += 1
                
                # Check cache first
                text_hash = hashlib.md5(medical_text.encode()).hexdigest()
                if text_hash in self._embedding_cache:
                    self._cache_hits += 1
                    # Move to end for LRU behavior
                    embedding = self._embedding_cache.pop(text_hash)
                    self._embedding_cache[text_hash] = embedding
                    logger.debug(f"Cache hit for medical embedding: {text_hash[:8]}")
                    return embedding.copy()
            
            # Generate embedding using the loaded model (PubMedBERT or BioBERT-large)
            if hasattr(self, 'use_pubmedbert') and self.use_pubmedbert:
                # PubMedBERT model
                embedding = self._create_pubmedbert_embedding(medical_text)
            else:
                # BioBERT-large fallback model
                embedding = self._create_biobert_embedding(medical_text)
            
            # Cache the result (thread-safe)
            self._cache_embedding(text_hash, embedding)
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to create medical embedding: {str(e)}")
            # Return zero vector as fallback
            return np.zeros(self.embedding_dim)
    
    def _cache_embedding(self, text_hash: str, embedding: np.ndarray):
        """Cache an embedding with proper LRU eviction (thread-safe)"""
        with self._cache_lock:
            # If cache is full, remove least recently used entry
            if len(self._embedding_cache) >= self._cache_max_size:
                # Remove oldest entry (FIFO in OrderedDict)
                oldest_key, _ = self._embedding_cache.popitem(last=False)
                logger.debug(f"Evicted cache entry: {oldest_key[:8]}")
            
            self._embedding_cache[text_hash] = embedding.copy()
            logger.debug(f"Cached embedding: {text_hash[:8]}, cache size: {len(self._embedding_cache)}")
    
    def _create_pubmedbert_embedding(self, text: str) -> np.ndarray:
        """Create embedding using PubMedBERT model with improved chunking for long texts"""
        
        # Check if text needs chunking
        tokens = self.tokenizer.encode(text, add_special_tokens=False)
        max_tokens = 510  # Leave room for [CLS] and [SEP] tokens
        
        if len(tokens) <= max_tokens:
            # Text fits in one chunk
            return self._create_single_embedding(text)
        else:
            # Text needs chunking - split and average embeddings
            return self._create_chunked_embedding(text, max_tokens)
    
    def _create_biobert_embedding(self, text: str) -> np.ndarray:
        """Create embedding using BioBERT-large fallback model with improved chunking for long texts"""
        
        # Check if text needs chunking
        tokens = self.tokenizer.encode(text, add_special_tokens=False)
        max_tokens = 510  # Leave room for [CLS] and [SEP] tokens
        
        if len(tokens) <= max_tokens:
            # Text fits in one chunk
            return self._create_single_embedding(text)
        else:
            # Text needs chunking - split and average embeddings
            return self._create_chunked_embedding(text, max_tokens)
    
    def _create_single_embedding(self, text: str) -> np.ndarray:
        """Create embedding for a single text that fits within token limit"""
        # Tokenize text
        inputs = self.tokenizer(
            text,
            return_tensors='pt',
            truncation=True,
            padding=True,
            max_length=512
        )
        
        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate embedding
        with torch.no_grad():
            outputs = self.model(**inputs)
            
            # Use CLS token embedding (first token)
            cls_embedding = outputs.last_hidden_state[:, 0, :]
            
            # Convert to numpy
            embedding = cls_embedding.cpu().numpy().flatten()
        
        return embedding
    
    def _create_chunked_embedding(self, text: str, max_tokens: int) -> np.ndarray:
        """Create embedding for long text by chunking and averaging with improved sentence boundary detection"""
        # Improved sentence splitting that handles medical abbreviations and decimals
        import re
        
        # Split on sentence boundaries but preserve medical abbreviations
        # This regex looks for periods followed by whitespace and capital letters
        # but excludes common medical abbreviations and decimal numbers
        sentence_pattern = r'(?<!\b(?:Dr|Mr|Mrs|Ms|Prof|vs|etc|mg|ml|kg|lb|oz|ft|in|cm|mm|bp|hr|min|sec|temp|resp|wt|ht|BMI|CBC|BUN|ALT|AST|HDL|LDL|TSH|PSA|HbA1c|A1C|IV|IM|PO|PRN|BID|TID|QID|QD|QOD|AM|PM|ER|ICU|OR|ED|CT|MRI|EKG|ECG|EEG|CXR|US|UA|CBC|CMP|BMP|PT|PTT|INR|ESR|CRP)\.)(?<!\d\.)\.(?=\s+[A-Z])'
        
        sentences = re.split(sentence_pattern, text)
        
        # If regex splitting fails, fall back to simple period splitting
        if len(sentences) <= 1:
            sentences = text.split('. ')
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            sentence_tokens = len(self.tokenizer.encode(sentence, add_special_tokens=False))
            
            if current_tokens + sentence_tokens <= max_tokens and current_chunk:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
            else:
                # Start new chunk
                if current_chunk:
                    chunks.append('. '.join(current_chunk))
                current_chunk = [sentence]
                current_tokens = sentence_tokens
        
        # Add final chunk
        if current_chunk:
            chunks.append('. '.join(current_chunk))
        
        # Generate embeddings for each chunk
        chunk_embeddings = []
        for chunk in chunks:
            if chunk.strip():  # Only process non-empty chunks
                embedding = self._create_single_embedding(chunk)
                chunk_embeddings.append(embedding)
        
        if not chunk_embeddings:
            # Fallback for edge cases
            return np.zeros(self.embedding_dim)
        
        # Average the chunk embeddings
        averaged_embedding = np.mean(chunk_embeddings, axis=0)
        return averaged_embedding
    
    def create_medical_embeddings_batch(self, medical_profiles: List[Dict[str, Any]]) -> np.ndarray:
        """
        Create embeddings for multiple medical profiles efficiently using batching with chunking support
        """
        try:
            if not medical_profiles:
                return np.array([])
            
            # Convert all profiles to text
            medical_texts = [self._medical_profile_to_text(profile) for profile in medical_profiles]
            
            # Generate embeddings using the loaded model
            if hasattr(self, 'use_pubmedbert') and self.use_pubmedbert:
                # PubMedBERT model - implement batching with chunking support
                embeddings = self._create_pubmedbert_embeddings_batch(medical_texts)
            else:
                # BioBERT-large fallback model - implement batching with chunking support
                embeddings = self._create_biobert_embeddings_batch(medical_texts)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to create batch medical embeddings: {str(e)}")
            # Return zero vectors as fallback
            return np.zeros((len(medical_profiles), self.embedding_dim))
    
    def _create_pubmedbert_embeddings_batch(self, texts: List[str], batch_size: int = 8) -> np.ndarray:
        """Create embeddings for multiple texts using PubMedBERT with batching and chunking support"""
        all_embeddings = []
        
        # Process each text individually to handle chunking properly
        for text in texts:
            embedding = self._create_pubmedbert_embedding(text)
            all_embeddings.append(embedding)
        
        return np.array(all_embeddings)
    
    def _create_biobert_embeddings_batch(self, texts: List[str], batch_size: int = 8) -> np.ndarray:
        """Create embeddings for multiple texts using BioBERT-large with batching and chunking support"""
        # BioBERT-large uses the same process as PubMedBERT (both are transformers models)
        all_embeddings = []
        
        # Process each text individually to handle chunking properly
        for text in texts:
            embedding = self._create_biobert_embedding(text)
            all_embeddings.append(embedding)
        
        return np.array(all_embeddings)
    
    def _medical_profile_to_text(self, profile: Dict[str, Any]) -> str:
        """
        Convert medical profile to structured text for embedding
        """
        text_parts = []
        
        # Current medications
        medications = profile.get('medications', [])
        if medications:
            med_texts = []
            for med in medications:
                if isinstance(med, dict):
                    med_text = f"{med.get('name', '')} {med.get('dosage', '')} {med.get('frequency', '')}"
                else:
                    med_text = str(med)
                med_texts.append(med_text.strip())
            
            if med_texts:
                text_parts.append(f"Current medications: {', '.join(med_texts)}")
        
        # Recent symptoms
        symptoms = profile.get('recent_symptoms', [])
        if symptoms:
            symptom_texts = []
            for symptom in symptoms:
                if isinstance(symptom, dict):
                    symptom_text = f"{symptom.get('symptom', '')} {symptom.get('severity', '')}"
                else:
                    symptom_text = str(symptom)
                symptom_texts.append(symptom_text.strip())
            
            if symptom_texts:
                text_parts.append(f"Recent symptoms: {', '.join(symptom_texts)}")
        
        # Health conditions
        conditions = profile.get('health_conditions', [])
        if conditions:
            condition_texts = []
            for condition in conditions:
                if isinstance(condition, dict):
                    condition_text = condition.get('condition', str(condition))
                else:
                    condition_text = str(condition)
                condition_texts.append(condition_text.strip())
            
            if condition_texts:
                text_parts.append(f"Health conditions: {', '.join(condition_texts)}")
        
        # Lab results (recent)
        lab_results = profile.get('lab_results', [])
        if lab_results:
            lab_texts = []
            for lab in lab_results[-5:]:  # Only recent 5 results
                if isinstance(lab, dict):
                    lab_text = f"{lab.get('test', '')} {lab.get('value', '')} {lab.get('unit', '')}"
                else:
                    lab_text = str(lab)
                lab_texts.append(lab_text.strip())
            
            if lab_texts:
                text_parts.append(f"Recent lab results: {', '.join(lab_texts)}")
        
        # Combine all parts
        medical_text = ". ".join(text_parts)
        
        # Ensure we have some text
        if not medical_text.strip():
            medical_text = "No medical information available"
        
        return medical_text
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings using optimized NumPy operations
        """
        try:
            # Ensure embeddings are 1D
            emb1 = embedding1.flatten()
            emb2 = embedding2.flatten()
            
            # Calculate cosine similarity: dot product / (norm1 * norm2)
            dot_product = np.dot(emb1, emb2)
            norm1 = np.linalg.norm(emb1)
            norm2 = np.linalg.norm(emb2)
            
            # Avoid division by zero
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {str(e)}")
            return 0.0
    
    def find_similar_embeddings(self, target_embedding: np.ndarray, stored_embeddings: List[Tuple[np.ndarray, Dict]]) -> List[Tuple[float, Dict]]:
        """
        Find similar embeddings from stored medical situations
        """
        similarities = []
        
        for stored_embedding, metadata in stored_embeddings:
            similarity = self.calculate_similarity(target_embedding, stored_embedding)
            
            if similarity >= self.similarity_threshold:
                similarities.append((similarity, metadata))
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        return similarities
    
    def create_medical_hash(self, medical_profile: Dict[str, Any]) -> str:
        """
        Create hash of medical profile for caching and deduplication
        """
        # Create a normalized representation for hashing
        normalized = {
            "medications": sorted([
                f"{med.get('name', '')}-{med.get('dosage', '')}" 
                for med in medical_profile.get('medications', [])
                if isinstance(med, dict)
            ]),
            "symptoms": sorted([
                str(symptom.get('symptom', symptom) if isinstance(symptom, dict) else symptom)
                for symptom in medical_profile.get('recent_symptoms', [])
            ]),
            "conditions": sorted([
                str(condition.get('condition', condition) if isinstance(condition, dict) else condition)
                for condition in medical_profile.get('health_conditions', [])
            ])
        }
        
        # Create hash
        hash_string = json.dumps(normalized, sort_keys=True)
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def extract_medical_entities(self, medical_text: str) -> Dict[str, List[str]]:
        """
        Extract medical entities using NER with comprehensive medical entity recognition
        """
        if not self.nlp:
            logger.warning("Medical NER not available - returning empty entities")
            return {"drugs": [], "diseases": [], "symptoms": []}
        
        try:
            doc = self.nlp(medical_text)
            
            entities = {
                "drugs": [],
                "diseases": [],
                "symptoms": [],
                "procedures": [],
                "body_parts": []
            }
            
            for ent in doc.ents:
                entity_text = ent.text.lower().strip()
                if not entity_text:
                    continue
                
                # Map different entity types based on the NER model being used
                if hasattr(self.nlp, 'meta') and 'scispacy' in str(self.nlp.meta):
                    # scispaCy medical model entity mapping
                    if ent.label_ in ["CHEMICAL", "DRUG"]:
                        entities["drugs"].append(entity_text)
                    elif ent.label_ in ["DISEASE", "DISORDER", "CONDITION"]:
                        entities["diseases"].append(entity_text)
                    elif ent.label_ in ["SYMPTOM", "SIGN"]:
                        entities["symptoms"].append(entity_text)
                    elif ent.label_ in ["PROCEDURE", "TREATMENT"]:
                        entities["procedures"].append(entity_text)
                    elif ent.label_ in ["ANATOMY", "BODY_PART"]:
                        entities["body_parts"].append(entity_text)
                else:
                    # General English model - basic entity recognition
                    if ent.label_ in ["ORG"] and any(keyword in entity_text for keyword in ["hospital", "clinic", "pharmacy"]):
                        # Skip organization names for medical context
                        continue
                    elif ent.label_ in ["PERSON"] and any(title in entity_text for title in ["dr", "doctor", "physician"]):
                        # Skip doctor names
                        continue
                    else:
                        # For general model, try to classify based on context
                        if any(drug_keyword in entity_text for drug_keyword in ["mg", "ml", "tablet", "capsule", "pill"]):
                            entities["drugs"].append(entity_text)
                        elif any(symptom_keyword in entity_text for symptom_keyword in ["pain", "ache", "fever", "nausea"]):
                            entities["symptoms"].append(entity_text)
            
            # Remove duplicates while preserving order
            for key in entities:
                entities[key] = list(dict.fromkeys(entities[key]))
            
            logger.debug(f"Extracted medical entities: {len(entities['drugs'])} drugs, "
                        f"{len(entities['diseases'])} diseases, {len(entities['symptoms'])} symptoms")
            
            return entities
            
        except Exception as e:
            logger.error(f"Failed to extract medical entities: {str(e)}")
            return {"drugs": [], "diseases": [], "symptoms": [], "procedures": [], "body_parts": []}
    
    def clear_cache(self):
        """Clear the embedding cache (thread-safe)"""
        with self._cache_lock:
            self._embedding_cache.clear()
            self._cache_hits = 0
            self._cache_requests = 0
            logger.info("Embedding cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics (thread-safe)"""
        with self._cache_lock:
            return {
                "cache_size": len(self._embedding_cache),
                "max_cache_size": self._cache_max_size,
                "cache_hits": self._cache_hits,
                "cache_requests": self._cache_requests,
                "cache_hit_ratio": self._cache_hits / max(self._cache_requests, 1)
            }

# Global instance
medical_embedding_service = MedicalEmbeddingService() 