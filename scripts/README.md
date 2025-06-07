# Medical Data Hub - Testing & Demo Scripts

This directory contains scripts and tools for testing, demo creation, and launch preparation for the Medical Data Hub MVP.

## Quick Start

### 1. Install Dependencies
```bash
python3 -m pip install -r scripts/requirements.txt
```

### 2. Generate Sample Data
```bash
python3 scripts/generate_sample_data.py
```

This will create:
- `sample_data/prescriptions/` - Sample prescription PDFs
- `sample_data/lab_results/` - Sample lab result PDFs
- `sample_data/test_profiles/` - User profiles and test scenarios
- `sample_data/generation_summary.json` - Summary of generated data

### 3. Run E2E Testing
```bash
python3 scripts/e2e_testing_checklist.py
```

Follow the interactive prompts to systematically test all features.

## Files Overview

### Sample Data Generation
- **`generate_sample_data.py`** - Creates realistic medical documents and test profiles
- **`requirements.txt`** - Python dependencies for scripts

### Testing
- **`e2e_testing_checklist.py`** - Interactive E2E testing checklist for all features
- **Generated reports** - `e2e_test_report_YYYYMMDD_HHMMSS.json`

### Marketing & Demo
- **`demo_video_script.md`** - Comprehensive demo video script with scenes and timing
- **Launch plan** - See `../memory-bank/mvp-launch-plan.md`

## Sample Data Details

### Generated User Profiles

#### 1. Diabetes Management (Sarah Martinez, 45)
- **Conditions**: Type 2 Diabetes, Hypertension
- **Medications**: Metformin, Lisinopril
- **Documents**: 4 total (2 prescriptions, 2 lab results)
- **Health Readings**: 10 glucose and BP readings over 3 months

#### 2. Heart Disease (Robert Thompson, 62)
- **Conditions**: Hypertension, High Cholesterol, CAD
- **Medications**: Lisinopril, Atorvastatin, Aspirin
- **Documents**: 4 total (3 prescriptions, 2 lab results)
- **Health Readings**: 10 BP readings over 3 months

#### 3. Preventive Care (Maria Gonzalez, 35)
- **Conditions**: Hypothyroidism
- **Medications**: Levothyroxine
- **Documents**: 3 total (1 prescription, 2 lab results)
- **Health Readings**: None (preventive care focused)

### Sample Documents Generated
- **6 Prescription PDFs** - Realistic prescription formats with doctor letterheads
- **6 Lab Result PDFs** - Professional lab report formats with test values and reference ranges
- **Complete metadata** - Patient names, doctors, dates, medication details

### Sample Queries for Testing
```
"Show me all my medications"
"What lab tests did I have last month?"
"List my prescriptions from Dr. Johnson"
"How has my blood pressure changed over time?"
"Show my glucose readings from the past 3 months"
"What's my latest cholesterol level?"
"Which medications am I taking for blood pressure?"
"When was my last HbA1c test and what was the result?"
"Show me all lab results that were outside normal range"
"Are any of my medications interacting?"
"What should I know about taking these medications together?"
"Any side effects I should watch for?"
"Find prescription from January 2024"
"Show lab results from HealthLab Analytics"
"What did my cardiologist prescribe?"
```

## E2E Testing Categories

### 1. Authentication & User Management (5 tests)
- User registration and login
- Credential validation
- Session persistence
- Logout functionality

### 2. Document Upload & Processing (6 tests)
- PDF and image upload
- Processing status monitoring
- OCR accuracy verification
- Data correction workflow

### 3. Data Viewing & Management (6 tests)
- Medication management
- Health reading tracking
- Document organization
- Search and filtering

### 4. AI Features (6 tests)
- OCR accuracy testing
- Natural language queries
- Drug interaction notifications
- Health trend alerts

### 5. User Interface & Experience (5 tests)
- Navigation flow
- Form validation
- Loading states
- Error handling
- Responsive design

### 6. Performance & Reliability (5 tests)
- App launch time (<3s target)
- Document processing time (<30s target)
- Query response time (<3s target)
- Data loading performance (<1s target)
- Memory usage monitoring

### 7. Security & Privacy (4 tests)
- Data encryption verification
- Authentication token handling
- Access control validation
- Privacy disclaimer compliance

## Using Sample Data for Demo Video

### Recommended Testing Flow
1. **Start with diabetes_management profile**
2. **Upload `diabetes_management_prescription_1.pdf`**
3. **Review extracted Metformin details**
4. **Add manual health readings (glucose, BP)**
5. **Test queries**: "Show my diabetes medications"
6. **Add medication that triggers interaction alert**
7. **Demonstrate notification system**

### Key Demo Scenes
- Document upload and AI processing
- Data review and correction
- Natural language querying
- Health trend visualization
- Drug interaction notifications
- Complete medical profile overview

## Performance Targets

### Processing Times
- **App Launch**: <3 seconds
- **Document Processing**: <30 seconds end-to-end
- **Query Response**: <3 seconds
- **Data Loading**: <1 second for cached data

### Accuracy Targets
- **OCR Accuracy**: >90% for typed text, >70% for handwritten
- **AI Structuring**: >95% for medication names and dosages
- **Query Understanding**: >90% for common health queries

## Troubleshooting

### Common Issues
1. **ReportLab not found**: Run `python3 -m pip install reportlab`
2. **Permission denied**: Ensure scripts are executable with `chmod +x scripts/*.py`
3. **Sample data not generated**: Check that output directory is writable

### Dependencies
- **Python 3.11+** (required for backend compatibility)
- **ReportLab 4.4.1+** (PDF generation)
- **Pillow 9.0.0+** (image processing, auto-installed with ReportLab)

## Next Steps After Sample Data Generation

1. **Review generated documents** - Check `sample_data/` directories
2. **Test document upload** - Use mobile app to upload sample PDFs
3. **Verify OCR accuracy** - Compare extracted vs original data
4. **Test AI features** - Run natural language queries
5. **Record demo video** - Follow script in `demo_video_script.md`
6. **Run E2E testing** - Complete full testing checklist
7. **Launch beta program** - See launch plan in `memory-bank/`

## Support

For issues with scripts or testing:
1. Check this README for troubleshooting
2. Review the generated sample data structure
3. Verify all dependencies are installed
4. Check Python version compatibility (3.11+)

The scripts are designed to work together to provide a comprehensive testing and demo environment for your Medical Data Hub MVP. 