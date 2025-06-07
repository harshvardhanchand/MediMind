#!/usr/bin/env python3
"""
Sample Medical Document Generator for MVP Testing
Creates realistic but fictional medical documents for testing the Medical Data Hub
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import random

class SampleDataGenerator:
    def __init__(self, output_dir="sample_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "prescriptions").mkdir(exist_ok=True)
        (self.output_dir / "lab_results").mkdir(exist_ok=True)
        (self.output_dir / "specialist_reports").mkdir(exist_ok=True)
        (self.output_dir / "test_profiles").mkdir(exist_ok=True)
        
        self.styles = getSampleStyleSheet()
        self.sample_data = self._generate_sample_data()
    
    def _generate_sample_data(self):
        """Generate all sample medical data"""
        return {
            "doctors": [
                {"name": "Dr. Sarah Johnson", "specialty": "Cardiology", "practice": "Metro Cardiology"},
                {"name": "Dr. Michael Chen", "specialty": "Endocrinology", "practice": "Endocrine Associates"},
                {"name": "Dr. Lisa Rodriguez", "specialty": "Family Medicine", "practice": "Family Care Center"},
                {"name": "Dr. James Wilson", "specialty": "Internal Medicine", "practice": "Internal Med Group"},
                {"name": "Dr. Patricia Adams", "specialty": "Cardiology", "practice": "Heart Center"},
                {"name": "Dr. Robert Kim", "specialty": "Dermatology", "practice": "Skin Specialists"}
            ],
            "medications": [
                {"name": "Lisinopril", "dosage": "10mg", "frequency": "once daily", "condition": "hypertension"},
                {"name": "Metformin", "dosage": "500mg", "frequency": "twice daily with meals", "condition": "diabetes"},
                {"name": "Atorvastatin", "dosage": "20mg", "frequency": "once daily at bedtime", "condition": "cholesterol"},
                {"name": "Amlodipine", "dosage": "5mg", "frequency": "once daily", "condition": "hypertension"},
                {"name": "Amoxicillin", "dosage": "875mg", "frequency": "twice daily", "condition": "infection", "duration": "10 days"},
                {"name": "Insulin Glargine", "dosage": "20 units", "frequency": "once daily at bedtime", "condition": "diabetes"},
                {"name": "Aspirin", "dosage": "81mg", "frequency": "once daily", "condition": "cardioprotective"},
                {"name": "Levothyroxine", "dosage": "75mcg", "frequency": "once daily on empty stomach", "condition": "hypothyroidism"}
            ],
            "lab_tests": {
                "comprehensive_metabolic": {
                    "glucose": {"value": 95, "unit": "mg/dL", "range": "70-100"},
                    "creatinine": {"value": 1.0, "unit": "mg/dL", "range": "0.6-1.2"},
                    "bun": {"value": 18, "unit": "mg/dL", "range": "7-20"},
                    "sodium": {"value": 140, "unit": "mEq/L", "range": "136-145"}
                },
                "lipid_panel": {
                    "total_cholesterol": {"value": 210, "unit": "mg/dL", "range": "<200"},
                    "hdl": {"value": 45, "unit": "mg/dL", "range": ">40"},
                    "ldl": {"value": 145, "unit": "mg/dL", "range": "<100"},
                    "triglycerides": {"value": 150, "unit": "mg/dL", "range": "<150"}
                },
                "hba1c": {
                    "hba1c": {"value": 6.2, "unit": "%", "range": "<5.7"}
                },
                "cbc": {
                    "wbc": {"value": 7200, "unit": "/μL", "range": "4,500-11,000"},
                    "rbc": {"value": 4.5, "unit": "million/μL", "range": "4.0-5.5"},
                    "hemoglobin": {"value": 14.2, "unit": "g/dL", "range": "12-16"},
                    "hematocrit": {"value": 42, "unit": "%", "range": "36-48"}
                }
            },
            "patients": [
                {
                    "name": "Sarah Martinez",
                    "age": 45,
                    "conditions": ["Type 2 Diabetes", "Hypertension"],
                    "medications": ["Metformin", "Lisinopril"],
                    "profile": "diabetes_management"
                },
                {
                    "name": "Robert Thompson",
                    "age": 62,
                    "conditions": ["Hypertension", "High Cholesterol", "CAD"],
                    "medications": ["Lisinopril", "Atorvastatin", "Aspirin"],
                    "profile": "heart_disease"
                },
                {
                    "name": "Maria Gonzalez",
                    "age": 35,
                    "conditions": ["Hypothyroidism"],
                    "medications": ["Levothyroxine"],
                    "profile": "preventive_care"
                }
            ]
        }
    
    def generate_prescription_pdf(self, patient_name, doctor, medications, date, filename):
        """Generate a prescription document"""
        doc = SimpleDocTemplate(
            str(self.output_dir / "prescriptions" / f"{filename}.pdf"),
            pagesize=letter,
            rightMargin=72, leftMargin=72,
            topMargin=72, bottomMargin=18
        )
        
        story = []
        
        # Header
        header_style = self.styles['Title']
        story.append(Paragraph(f"<b>{doctor['practice']}</b>", header_style))
        story.append(Paragraph(f"{doctor['name']}, MD - {doctor['specialty']}", self.styles['Normal']))
        story.append(Paragraph("123 Medical Center Drive, Health City, HC 12345", self.styles['Normal']))
        story.append(Paragraph("Phone: (555) 123-4567 | Fax: (555) 123-4568", self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Patient Info
        story.append(Paragraph(f"<b>Date:</b> {date.strftime('%B %d, %Y')}", self.styles['Normal']))
        story.append(Paragraph(f"<b>Patient:</b> {patient_name}", self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Prescription Header
        story.append(Paragraph("<b>PRESCRIPTION</b>", self.styles['Heading2']))
        story.append(Spacer(1, 10))
        
        # Medications
        for i, med in enumerate(medications, 1):
            story.append(Paragraph(f"<b>{i}. {med['name']} {med['dosage']}</b>", self.styles['Normal']))
            story.append(Paragraph(f"   Take {med['frequency']}", self.styles['Normal']))
            if 'duration' in med:
                story.append(Paragraph(f"   Duration: {med['duration']}", self.styles['Normal']))
            story.append(Paragraph(f"   For: {med['condition']}", self.styles['Normal']))
            story.append(Spacer(1, 10))
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph("_" * 40, self.styles['Normal']))
        story.append(Paragraph(f"{doctor['name']}, MD", self.styles['Normal']))
        story.append(Paragraph(f"License #: MD{random.randint(10000, 99999)}", self.styles['Normal']))
        
        doc.build(story)
        return filename + ".pdf"
    
    def generate_lab_result_pdf(self, patient_name, lab_name, tests, date, filename):
        """Generate a lab result document"""
        doc = SimpleDocTemplate(
            str(self.output_dir / "lab_results" / f"{filename}.pdf"),
            pagesize=letter,
            rightMargin=72, leftMargin=72,
            topMargin=72, bottomMargin=18
        )
        
        story = []
        
        # Header
        story.append(Paragraph("<b>LABORATORY RESULTS</b>", self.styles['Title']))
        story.append(Paragraph("HealthLab Analytics", self.styles['Heading2']))
        story.append(Paragraph("456 Lab Plaza, Health City, HC 12345", self.styles['Normal']))
        story.append(Paragraph("Phone: (555) 987-6543", self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Patient Info
        story.append(Paragraph(f"<b>Patient:</b> {patient_name}", self.styles['Normal']))
        story.append(Paragraph(f"<b>Collection Date:</b> {date.strftime('%B %d, %Y')}", self.styles['Normal']))
        story.append(Paragraph(f"<b>Report Date:</b> {(date + timedelta(days=1)).strftime('%B %d, %Y')}", self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Test Results Table
        table_data = [['Test Name', 'Result', 'Unit', 'Reference Range', 'Flag']]
        
        for test_name, test_data in tests.items():
            flag = ""
            if "range" in test_data:
                range_val = test_data["range"]
                if "<" in range_val:
                    target = float(range_val.replace("<", ""))
                    if test_data["value"] > target:
                        flag = "HIGH"
                elif ">" in range_val:
                    target = float(range_val.replace(">", ""))
                    if test_data["value"] < target:
                        flag = "LOW"
            
            table_data.append([
                test_name.replace("_", " ").title(),
                str(test_data["value"]),
                test_data["unit"],
                test_data["range"],
                flag
            ])
        
        table = Table(table_data, colWidths=[2*inch, 1*inch, 1*inch, 1.5*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
        
        # Footer
        story.append(Paragraph("<b>Notes:</b>", self.styles['Normal']))
        story.append(Paragraph("Please consult with your healthcare provider to discuss these results.", self.styles['Normal']))
        story.append(Spacer(1, 10))
        story.append(Paragraph("Lab Director: Dr. Emily Watson, MD", self.styles['Normal']))
        
        doc.build(story)
        return filename + ".pdf"
    
    def generate_user_profiles(self):
        """Generate comprehensive test user profiles"""
        profiles = {}
        
        for patient in self.sample_data["patients"]:
            profile = {
                "personal_info": {
                    "name": patient["name"],
                    "age": patient["age"],
                    "conditions": patient["conditions"]
                },
                "documents": [],
                "medications": [],
                "health_readings": [],
                "test_scenarios": []
            }
            
            # Generate documents for this patient
            base_date = datetime.now() - timedelta(days=90)
            
            # Prescriptions
            patient_meds = [med for med in self.sample_data["medications"] 
                          if med["name"] in patient["medications"]]
            
            for i, med in enumerate(patient_meds):
                doc_date = base_date + timedelta(days=i*15)
                doctor = random.choice([d for d in self.sample_data["doctors"] 
                                     if d["specialty"] in ["Family Medicine", "Internal Medicine", "Cardiology", "Endocrinology"]])
                
                filename = f"{patient['profile']}_prescription_{i+1}"
                self.generate_prescription_pdf(
                    patient["name"], doctor, [med], doc_date, filename
                )
                
                profile["documents"].append({
                    "type": "prescription",
                    "filename": filename + ".pdf",
                    "date": doc_date.isoformat(),
                    "doctor": doctor["name"],
                    "medications": [med["name"]]
                })
                
                profile["medications"].append({
                    "name": med["name"],
                    "dosage": med["dosage"],
                    "frequency": med["frequency"],
                    "start_date": doc_date.isoformat(),
                    "prescribing_doctor": doctor["name"]
                })
            
            # Lab Results
            lab_tests = ["comprehensive_metabolic", "lipid_panel", "hba1c", "cbc"]
            for i, test_type in enumerate(lab_tests[:2]):  # Generate 2 lab results per patient
                doc_date = base_date + timedelta(days=30 + i*30)
                filename = f"{patient['profile']}_lab_{test_type}"
                
                self.generate_lab_result_pdf(
                    patient["name"], "HealthLab Analytics", 
                    self.sample_data["lab_tests"][test_type], doc_date, filename
                )
                
                profile["documents"].append({
                    "type": "lab_result",
                    "filename": filename + ".pdf",
                    "date": doc_date.isoformat(),
                    "lab": "HealthLab Analytics",
                    "tests": list(self.sample_data["lab_tests"][test_type].keys())
                })
            
            # Health Readings (simulate manual entries)
            reading_date = base_date
            for i in range(10):  # 10 readings over 3 months
                if "Diabetes" in patient["conditions"]:
                    profile["health_readings"].append({
                        "type": "glucose",
                        "value": random.randint(90, 140),
                        "unit": "mg/dL",
                        "date": reading_date.isoformat(),
                        "notes": "Fasting glucose reading"
                    })
                
                if "Hypertension" in patient["conditions"]:
                    profile["health_readings"].append({
                        "type": "blood_pressure",
                        "systolic": random.randint(120, 150),
                        "diastolic": random.randint(80, 95),
                        "unit": "mmHg",
                        "date": reading_date.isoformat()
                    })
                
                reading_date += timedelta(days=9)
            
            # Test Scenarios
            profile["test_scenarios"] = [
                {
                    "name": "Drug Interaction Test",
                    "description": f"Add Aspirin to {patient['name']}'s medications to test interaction alerts",
                    "expected_notification": "Drug interaction between blood thinners"
                },
                {
                    "name": "Natural Language Query Test",
                    "queries": [
                        f"Show {patient['name']}'s blood pressure readings from last month",
                        f"What medications did Dr. Johnson prescribe to {patient['name']}?",
                        f"When was {patient['name']}'s last lab test?"
                    ]
                },
                {
                    "name": "Trend Analysis Test",
                    "description": "Upload multiple lab results to test trend visualization",
                    "expected_behavior": "Show glucose/BP trends over time"
                }
            ]
            
            profiles[patient["profile"]] = profile
        
        # Save profiles
        with open(self.output_dir / "test_profiles" / "user_profiles.json", "w") as f:
            json.dump(profiles, f, indent=2, default=str)
        
        return profiles
    
    def generate_test_queries(self):
        """Generate sample queries for testing natural language processing"""
        queries = [
            # Basic retrieval queries
            "Show me all my medications",
            "What lab tests did I have last month?",
            "List my prescriptions from Dr. Johnson",
            
            # Trend and analysis queries
            "How has my blood pressure changed over time?",
            "Show my glucose readings from the past 3 months",
            "What's my latest cholesterol level?",
            
            # Complex queries
            "Which medications am I taking for blood pressure?",
            "When was my last HbA1c test and what was the result?",
            "Show me all lab results that were outside normal range",
            
            # Drug interaction queries
            "Are any of my medications interacting?",
            "What should I know about taking these medications together?",
            "Any side effects I should watch for?",
            
            # Document-specific queries
            "Find prescription from January 2024",
            "Show lab results from HealthLab Analytics",
            "What did my cardiologist prescribe?"
        ]
        
        with open(self.output_dir / "test_profiles" / "sample_queries.json", "w") as f:
            json.dump({"queries": queries}, f, indent=2)
        
        return queries
    
    def generate_all_sample_data(self):
        """Generate all sample data for testing"""
        print("Generating sample medical documents...")
        
        # Generate user profiles (this creates the PDFs)
        profiles = self.generate_user_profiles()
        print(f"Generated profiles for {len(profiles)} test users")
        
        # Generate test queries
        queries = self.generate_test_queries()
        print(f"Generated {len(queries)} sample queries")
        
        # Create summary
        summary = {
            "generation_date": datetime.now().isoformat(),
            "profiles": list(profiles.keys()),
            "total_documents": sum(len(p["documents"]) for p in profiles.values()),
            "total_medications": sum(len(p["medications"]) for p in profiles.values()),
            "total_health_readings": sum(len(p["health_readings"]) for p in profiles.values()),
            "sample_queries": len(queries),
            "directories": {
                "prescriptions": str(self.output_dir / "prescriptions"),
                "lab_results": str(self.output_dir / "lab_results"),
                "test_profiles": str(self.output_dir / "test_profiles")
            }
        }
        
        with open(self.output_dir / "generation_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        print("\n" + "="*50)
        print("SAMPLE DATA GENERATION COMPLETE")
        print("="*50)
        print(f"Output directory: {self.output_dir}")
        print(f"Total documents: {summary['total_documents']}")
        print(f"User profiles: {len(profiles)}")
        print(f"Sample queries: {len(queries)}")
        print("\nReady for E2E testing!")
        
        return summary

def main():
    """Main function to generate all sample data"""
    generator = SampleDataGenerator()
    summary = generator.generate_all_sample_data()
    
    print("\nNext steps:")
    print("1. Review generated documents in sample_data/ directory")
    print("2. Use test_profiles/user_profiles.json for E2E testing")
    print("3. Test with sample_queries.json for natural language processing")
    print("4. Upload documents through your mobile app to test OCR and AI processing")

if __name__ == "__main__":
    main() 