"""
OCR Quality Validation Service
Validates Google Document AI OCR results based on confidence scores
"""

import logging
import os
from typing import Dict, Any, Optional
from google.cloud import documentai

logger = logging.getLogger(__name__)

class OCRValidationConfig:
    """Configuration for OCR validation thresholds"""
    
    DOCUMENT_TYPE_THRESHOLDS = {
        "prescription": 0.85,
        "lab_result": 0.80,
        "imaging_report": 0.75,
        "consultation_note": 0.75,
        "discharge_summary": 0.80,
        "insurance_card": 0.70,
        "other": 0.75
    }
    
    ABSOLUTE_MINIMUM_CONFIDENCE = 0.70
    
    def __init__(self):
        """Initialize with hardcoded defaults and optional environment overrides"""
        self.thresholds = self.DOCUMENT_TYPE_THRESHOLDS.copy()
        self.absolute_minimum = self.ABSOLUTE_MINIMUM_CONFIDENCE
        
        global_threshold = self._get_float_from_env("OCR_CONFIDENCE_THRESHOLD")
        if global_threshold is not None:
            for doc_type in self.thresholds:
                self.thresholds[doc_type] = global_threshold
        
        overrides_found = []
        for doc_type in self.thresholds:
            env_key = f"OCR_THRESHOLD_{doc_type.upper()}"
            specific_threshold = self._get_float_from_env(env_key)
            if specific_threshold is not None:
                self.thresholds[doc_type] = specific_threshold
                overrides_found.append(f"{doc_type}={specific_threshold:.1%}")
        
        abs_min_override = self._get_float_from_env("OCR_ABSOLUTE_MINIMUM")
        if abs_min_override is not None:
            self.absolute_minimum = abs_min_override
            overrides_found.append(f"absolute_min={abs_min_override:.1%}")
    
    def _get_float_from_env(self, env_key: str) -> Optional[float]:
        """Safely get float value from environment variable"""
        try:
            value = os.getenv(env_key)
            if value is not None:
                float_val = float(value)
                if 0.0 <= float_val <= 1.0:
                    return float_val
                else:
                    logger.warning(f"Invalid {env_key} value {value} (must be 0.0-1.0), using default")
            return None
        except (ValueError, TypeError):
            logger.warning(f"Invalid {env_key} value '{value}' (not a valid float), using default")
            return None
    
    def get_threshold(self, document_type: str) -> float:
        """Get confidence threshold for document type"""
        return self.thresholds.get(document_type.lower(), self.thresholds["other"])
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration for debugging/admin"""
        env_overrides = {}
        
        if os.getenv("OCR_CONFIDENCE_THRESHOLD"):
            env_overrides["OCR_CONFIDENCE_THRESHOLD"] = os.getenv("OCR_CONFIDENCE_THRESHOLD")
        
        for doc_type in self.DOCUMENT_TYPE_THRESHOLDS:
            env_key = f"OCR_THRESHOLD_{doc_type.upper()}"
            if os.getenv(env_key):
                env_overrides[env_key] = os.getenv(env_key)
        
        if os.getenv("OCR_ABSOLUTE_MINIMUM"):
            env_overrides["OCR_ABSOLUTE_MINIMUM"] = os.getenv("OCR_ABSOLUTE_MINIMUM")
        
        return {
            "active_thresholds": self.thresholds,
            "absolute_minimum": self.absolute_minimum,
            "hardcoded_defaults": self.DOCUMENT_TYPE_THRESHOLDS,
            "environment_overrides": env_overrides,
            "has_overrides": len(env_overrides) > 0
        }


def extract_document_ai_confidence(doc_ai_result: documentai.Document) -> float:
    """
    Extract overall confidence score from Document AI result
    
    Args:
        doc_ai_result: Document AI processed document
        
    Returns:
        Average confidence score (0.0 to 1.0)
    """
    if not doc_ai_result or not doc_ai_result.pages:
        return 0.0
    
    confidence_scores = []
    
    for page in doc_ai_result.pages:
        # Tokens have the highest granularity and usually the most reliable confidence
        if hasattr(page, 'tokens') and page.tokens:
            for token in page.tokens:
                if hasattr(token, 'layout') and hasattr(token.layout, 'confidence'):
                    confidence_scores.append(token.layout.confidence)
        
        # If no tokens, fall back to paragraphs
        elif hasattr(page, 'paragraphs') and page.paragraphs:
            for paragraph in page.paragraphs:
                if hasattr(paragraph, 'layout') and hasattr(paragraph.layout, 'confidence'):
                    confidence_scores.append(paragraph.layout.confidence)
        
        # If no paragraphs, fall back to lines
        elif hasattr(page, 'lines') and page.lines:
            for line in page.lines:
                if hasattr(line, 'layout') and hasattr(line.layout, 'confidence'):
                    confidence_scores.append(line.layout.confidence)
        
        # If no lines, fall back to blocks
        elif hasattr(page, 'blocks') and page.blocks:
            for block in page.blocks:
                if hasattr(block, 'layout') and hasattr(block.layout, 'confidence'):
                    confidence_scores.append(block.layout.confidence)
    
    if confidence_scores:
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        logger.info(f"Extracted {len(confidence_scores)} confidence scores, average: {avg_confidence:.3f}")
        return avg_confidence
    else:
        # This should be extremely rare - Google Document AI almost always provides confidence scores
        logger.error("No confidence scores found in Document AI result - this indicates a serious issue with OCR processing")
        return 0.0  # Changed from 0.8 to 0.0 to flag the issue


def validate_ocr_confidence(
    doc_ai_result: documentai.Document, 
    document_type: str = "other"
) -> Dict[str, Any]:
    """
    Validate OCR result confidence against document type threshold
    
    Args:
        doc_ai_result: Document AI processed document
        document_type: Type of document for threshold selection
        
    Returns:
        Dictionary with validation results:
        {
            "is_valid": bool,
            "confidence": float,
            "threshold": float, 
            "document_type": str,
            "message": str
        }
    """
    
    config = OCRValidationConfig()
    
    confidence = extract_document_ai_confidence(doc_ai_result)
    
    threshold = config.get_threshold(document_type)
    
    is_valid = confidence >= threshold
    
    if is_valid:
        message = f"OCR quality acceptable (confidence: {confidence:.1%}, required: {threshold:.1%})"
        quality_level = "excellent" if confidence >= 0.95 else "good" if confidence >= 0.85 else "acceptable"
        recommendation = "Document processed successfully"
    else:
        quality_level = "poor"
        if confidence < config.absolute_minimum:
            message = f"OCR quality unacceptable (confidence: {confidence:.1%}, minimum: {config.absolute_minimum:.1%})"
            recommendation = "Please retake the photo with better lighting and focus"
        else:
            message = f"OCR quality too low (confidence: {confidence:.1%}, required: {threshold:.1%})"
            # Document-specific recommendations
            if document_type == "prescription":
                recommendation = "For prescriptions, ensure all medication names and dosages are clearly visible"
            elif document_type == "lab_result":
                recommendation = "For lab results, make sure all numbers and test names are in sharp focus"
            elif document_type in ["discharge_summary", "consultation_note"]:
                recommendation = "For medical notes, ensure handwriting is legible or use typed documents when possible"
            elif document_type == "insurance_card":
                recommendation = "For insurance cards, avoid glare and ensure all text is readable"
            else:
                recommendation = "Please retake with better lighting, focus, and straight-on angle"
    
    return {
        "is_valid": is_valid,
        "confidence": confidence,
        "threshold": threshold,
        "document_type": document_type,
        "message": message,
        "quality_level": quality_level,
        "recommendation": recommendation,
        "absolute_minimum": config.absolute_minimum
    }


def is_ocr_acceptable(doc_ai_result: documentai.Document, document_type: str = "other") -> bool:
    """Simple boolean check for OCR acceptability"""
    return validate_ocr_confidence(doc_ai_result, document_type)["is_valid"]


def test_validation_config():
    """Test function to verify configuration is working correctly"""
    config = OCRValidationConfig()
    summary = config.get_config_summary()
    return summary


def get_validation_summary(validation_result: Dict[str, Any]) -> str:
    """
    Generate a concise summary of OCR validation results for logging
    
    Args:
        validation_result: Result from validate_ocr_confidence()
        
    Returns:
        Summary string for logging
    """
    status = "PASS" if validation_result["is_valid"] else "FAIL"
    confidence = validation_result["confidence"]
    threshold = validation_result["threshold"]
    doc_type = validation_result["document_type"]
    
    return f"{status} - {doc_type}: {confidence:.1%} (req: {threshold:.1%})"


if __name__ == "__main__":
    test_validation_config() 