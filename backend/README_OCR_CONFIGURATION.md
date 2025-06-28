# OCR Quality Validation Configuration

This document explains how to configure OCR confidence thresholds for document processing quality control.

## Overview

The system validates Google Document AI OCR results before expensive LLM processing to:
- **Save costs** by rejecting poor quality documents early
- **Improve accuracy** by ensuring only readable documents are processed  
- **Better UX** by providing clear feedback on document quality issues

## Default Thresholds (Research-Based)

| Document Type | Threshold | Rationale |
|---------------|-----------|-----------|
| `prescription` | **85%** | High - medication safety critical |
| `lab_result` | **80%** | High - numeric values important |
| `discharge_summary` | **80%** | High - important medical information |
| `imaging_report` | **75%** | Medium - mostly descriptive text |
| `consultation_note` | **75%** | Medium - often handwritten |
| `other` | **75%** | Default medium threshold |

## Environment Variable Configuration

### Global Threshold Override
```bash
# Override all document types
OCR_CONFIDENCE_THRESHOLD=0.80
```

### Document-Type Specific Thresholds
```bash
# Specific overrides (more restrictive)
OCR_THRESHOLD_PRESCRIPTION=0.90
OCR_THRESHOLD_LAB_RESULT=0.85
OCR_THRESHOLD_IMAGING_REPORT=0.70
OCR_THRESHOLD_CONSULTATION_NOTE=0.70
OCR_THRESHOLD_DISCHARGE_SUMMARY=0.85
OCR_THRESHOLD_OTHER=0.75
```

### Production Examples

**Conservative (High Quality)**:
```bash
OCR_CONFIDENCE_THRESHOLD=0.85
```

**Lenient (Accept More Documents)**:
```bash
OCR_CONFIDENCE_THRESHOLD=0.70
```

**Balanced (Recommended)**:
```bash
# Use defaults (no environment variables)
# prescription=0.85, lab_result=0.80, others=0.75
```

## Quality Levels

| Confidence Range | Quality Level | Typical Scenarios |
|------------------|---------------|-------------------|
| **90-100%** | Excellent | Clean printed documents, high-res scans |
| **80-89%** | Good | Standard printed documents, decent photos |
| **70-79%** | Fair | Lower quality scans, some handwriting |
| **50-69%** | Poor | Blurry photos, poor lighting, faded text |
| **0-49%** | Very Poor | Severely damaged or illegible documents |

## Error Messages

When documents are rejected, users receive specific guidance:

### High Quality Issues (60-79% confidence)
> "Document quality is close to acceptable. Consider uploading a clearer version for prescription documents."

### Medium Quality Issues (30-59% confidence)  
> "Document quality is too low. Please upload a clearer scan or photo with better lighting."

### Low Quality Issues (<30% confidence)
> "Document appears to be very low quality. Please ensure it's a clear, readable medical document and try uploading again."

## Monitoring & Logging

The system logs detailed OCR validation results:

```
✅ OCR passed: 87% confidence for prescription (threshold: 85%)
❌ OCR failed: 72% confidence for prescription (threshold: 85%)
```

## Cost Impact Analysis

### Before OCR Validation
- Poor OCR (45% confidence) → Gemini LLM call ($0.02) → Poor results
- **Result**: Wasted money + confused users

### After OCR Validation  
- Poor OCR (45% confidence) → **REJECTED** → Ask user to re-upload
- **Result**: Save money + better user experience

### Estimated Savings
- **10-20% reduction** in LLM API costs
- **50% reduction** in user support tickets about poor extraction results

## Tuning Recommendations

### If Too Many Documents Rejected
1. **Lower thresholds** by 5-10%:
   ```bash
   OCR_CONFIDENCE_THRESHOLD=0.70
   ```

2. **Document-specific tuning**:
   ```bash
   OCR_THRESHOLD_CONSULTATION_NOTE=0.65  # Often handwritten
   ```

### If Quality Issues Persist
1. **Raise thresholds** by 5-10%:
   ```bash
   OCR_CONFIDENCE_THRESHOLD=0.85
   ```

2. **Be more strict with critical documents**:
   ```bash
   OCR_THRESHOLD_PRESCRIPTION=0.90
   OCR_THRESHOLD_LAB_RESULT=0.85
   ```

## Development/Testing

### Disable Validation (Development Only)
```bash
OCR_CONFIDENCE_THRESHOLD=0.0
```

### Conservative Testing
```bash
OCR_CONFIDENCE_THRESHOLD=0.90
```

## Implementation Details

- **Early rejection**: Documents are rejected before LLM processing
- **Status tracking**: Failed documents marked as `ProcessingStatus.FAILED`
- **No reprocessing**: Failed documents won't be reprocessed automatically
- **User feedback**: Clear error messages with specific recommendations

## Integration with Frontend

The frontend automatically handles `OCR_QUALITY_TOO_LOW` errors with:
- 📷 **Clear error icons**
- 💡 **Actionable tips** for better photos
- 🔄 **Easy re-upload** workflow

## Best Practices

1. **Start with defaults** - they're research-based
2. **Monitor rejection rates** - adjust if too high/low
3. **Document-specific tuning** - prescriptions need higher quality
4. **Test with real documents** - use actual user uploads for validation
5. **Regular review** - adjust thresholds based on user feedback

---

For questions or issues, check the application logs for detailed OCR validation results. 