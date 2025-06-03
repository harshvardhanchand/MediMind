"""
Medical Embedding Service using BioBERT
Handles creation and similarity search of medical situation embeddings
"""

import numpy as np
import json
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
import spacy

logger = logging.getLogger(__name__)

class MedicalEmbeddingService:
    """
    Medical embedding service using BioBERT for medical-specific understanding
    """
    
    def __init__(self):
        self.model_name = 'dmis-lab/biobert-v1.1'
        self.embedding_dim = 768  # BioBERT dimension
        self.similarity_threshold = 0.85
        
        # Initialize BioBERT
        self._init_biobert()
        
        # Initialize medical NER (optional - for entity extraction)
        self._init_medical_ner()
    
    def _init_biobert(self):
        """Initialize BioBERT model and tokenizer"""
        try:
            logger.info("Loading BioBERT model for medical embeddings...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.eval()  # Set to evaluation mode
            
            # Use GPU if available
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.model.to(self.device)
            
            logger.info(f"BioBERT loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load BioBERT: {str(e)}")
            # Fallback to sentence-transformers if BioBERT fails
            self._init_fallback_model()
    
    def _init_fallback_model(self):
        """Fallback to sentence-transformers if BioBERT fails"""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.embedding_dim = 384
            self.use_biobert = False
            logger.info("Using SentenceTransformer fallback model")
        except Exception as e:
            logger.error(f"Failed to load fallback model: {str(e)}")
            raise
    
    def _init_medical_ner(self):
        """Initialize medical NER for entity extraction (optional)"""
        try:
            # This is optional - comment out if you don't want to install spacy medical models
            # self.nlp = spacy.load("en_ner_bc5cdr_md")
            self.nlp = None
            logger.info("Medical NER initialized")
        except Exception as e:
            logger.warning(f"Medical NER not available: {str(e)}")
            self.nlp = None
    
    def create_medical_embedding(self, medical_profile: Dict[str, Any]) -> np.ndarray:
        """
        Create embedding vector from medical profile using BioBERT
        """
        try:
            # Convert medical profile to text
            medical_text = self._medical_profile_to_text(medical_profile)
            
            # Generate embedding using BioBERT
            if hasattr(self, 'use_biobert') and not self.use_biobert:
                # Fallback model
                embedding = self.model.encode(medical_text)
            else:
                # BioBERT model
                embedding = self._create_biobert_embedding(medical_text)
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to create medical embedding: {str(e)}")
            # Return zero vector as fallback
            return np.zeros(self.embedding_dim)
    
    def _create_biobert_embedding(self, text: str) -> np.ndarray:
        """Create embedding using BioBERT model"""
        
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
        Calculate cosine similarity between two embeddings
        """
        try:
            # Reshape for sklearn
            emb1 = embedding1.reshape(1, -1)
            emb2 = embedding2.reshape(1, -1)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(emb1, emb2)[0][0]
            
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
        Extract medical entities using NER (optional feature)
        """
        if not self.nlp:
            return {"drugs": [], "diseases": [], "symptoms": []}
        
        try:
            doc = self.nlp(medical_text)
            
            entities = {
                "drugs": [],
                "diseases": [],
                "symptoms": []
            }
            
            for ent in doc.ents:
                if ent.label_ == "CHEMICAL":
                    entities["drugs"].append(ent.text.lower())
                elif ent.label_ == "DISEASE":
                    entities["diseases"].append(ent.text.lower())
            
            return entities
            
        except Exception as e:
            logger.error(f"Failed to extract medical entities: {str(e)}")
            return {"drugs": [], "diseases": [], "symptoms": []}

# Global instance
medical_embedding_service = MedicalEmbeddingService() 