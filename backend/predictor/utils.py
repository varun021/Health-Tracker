from datetime import datetime
import csv
from io import StringIO, BytesIO
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, 
    Spacer, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Custom canvas to add page numbers and headers"""
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 9)
        self.drawRightString(
            7.5 * inch, 0.5 * inch,
            f"Page {self._pageNumber} of {page_count}"
        )
        self.drawString(
            0.75 * inch, 0.5 * inch,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )


class ReportGenerator:
    """Enhanced report generator with improved formatting and comprehensive data"""
    
    def __init__(self, submissions, include_personal=True, include_recommendations=True):
        self.submissions = submissions
        self.include_personal = include_personal
        self.include_recommendations = include_recommendations
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()

    def _add_custom_styles(self):
        """Add custom paragraph styles"""
        # Check if styles already exist to avoid KeyError
        if 'CustomTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='CustomTitle',
                parent=self.styles['Title'],
                fontSize=24,
                textColor=colors.HexColor('#1e3a8a'),
                spaceAfter=30,
                alignment=TA_CENTER
            ))
        
        if 'SectionHeader' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SectionHeader',
                parent=self.styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#1e40af'),
                spaceAfter=12,
                spaceBefore=12,
                leftIndent=0
            ))
        
        if 'SubHeader' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SubHeader',
                parent=self.styles['Heading3'],
                fontSize=11,
                textColor=colors.HexColor('#3b82f6'),
                spaceAfter=6,
                spaceBefore=6
            ))
        
        if 'ReportBodyText' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='ReportBodyText',
                parent=self.styles['Normal'],
                fontSize=10,
                alignment=TA_JUSTIFY,
                spaceAfter=6
            ))

    def _format_recommendations(self, text):
        """Format recommendation text into bullet points"""
        if not text:
            return []
        lines = text.strip().split('\n')
        formatted = []
        for line in lines:
            clean_line = line.strip().lstrip('•').lstrip('-').lstrip('*').strip()
            if clean_line:
                formatted.append(f"• {clean_line}")
        return formatted

    def generate_pdf(self):
        """Generate comprehensive PDF report"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )
        elements = []

        # Title Page
        elements.append(Paragraph("Medical Prediction Report", self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Report Info
        report_info = f"""
        <para alignment="center">
        <b>Report Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>
        <b>Total Predictions:</b> {self.submissions.count()}<br/>
        <b>Date Range:</b> {self.submissions.last().created_at.strftime('%Y-%m-%d')} to 
        {self.submissions.first().created_at.strftime('%Y-%m-%d')}
        </para>
        """
        elements.append(Paragraph(report_info, self.styles['ReportBodyText']))
        elements.append(Spacer(1, 0.3*inch))

        # Summary Statistics
        self._add_summary_statistics(elements)
        elements.append(PageBreak())

        # Detailed Predictions
        elements.append(Paragraph("Detailed Prediction History", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2*inch))

        for idx, submission in enumerate(self.submissions, 1):
            self._add_submission_detail(elements, submission, idx)
            if idx < self.submissions.count():
                elements.append(Spacer(1, 0.3*inch))
                elements.append(Paragraph("<hr/>", self.styles['Normal']))
                elements.append(Spacer(1, 0.2*inch))

        # Build PDF with custom canvas
        doc.build(elements, canvasmaker=NumberedCanvas)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    def _add_summary_statistics(self, elements):
        """Add summary statistics section to PDF"""
        elements.append(Paragraph("Summary Statistics", self.styles['SectionHeader']))
        
        # Calculate statistics
        total = self.submissions.count()
        severity_counts = {
            'NORMAL': self.submissions.filter(severity_category='NORMAL').count(),
            'MODERATE': self.submissions.filter(severity_category='MODERATE').count(),
            'RISKY': self.submissions.filter(severity_category='RISKY').count()
        }
        
        # Disease frequency
        from django.db.models import Count
        disease_freq = (self.submissions
            .values('primary_prediction__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:5])
        
        # Summary table
        summary_data = [
            ['Metric', 'Value'],
            ['Total Predictions', str(total)],
            ['Normal Cases', f"{severity_counts['NORMAL']} ({severity_counts['NORMAL']/total*100:.1f}%)"],
            ['Moderate Cases', f"{severity_counts['MODERATE']} ({severity_counts['MODERATE']/total*100:.1f}%)"],
            ['Risky Cases', f"{severity_counts['RISKY']} ({severity_counts['RISKY']/total*100:.1f}%)"],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Top diseases
        if disease_freq:
            elements.append(Paragraph("Most Common Conditions", self.styles['SubHeader']))
            disease_data = [['Rank', 'Disease', 'Occurrences']]
            for idx, item in enumerate(disease_freq, 1):
                disease_data.append([
                    str(idx),
                    item['primary_prediction__name'],
                    str(item['count'])
                ])
            
            disease_table = Table(disease_data, colWidths=[0.75*inch, 3.5*inch, 1.75*inch])
            disease_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            elements.append(disease_table)

    def _add_submission_detail(self, elements, submission, index):
        """Add detailed submission information to PDF"""
        # Header with date and index
        header_text = f"<b>Prediction #{index}</b> - {submission.created_at.strftime('%B %d, %Y at %I:%M %p')}"
        elements.append(Paragraph(header_text, self.styles['SubHeader']))
        
        # Patient Information
        if self.include_personal:
            patient_data = [
                ['Patient Information', ''],
                ['Name', submission.name or 'N/A'],
                ['Age', f"{submission.age} years" if submission.age else 'N/A'],
                ['Gender', submission.get_gender_display() if submission.gender else 'N/A'],
            ]
            
            # Add physical metrics if available
            if submission.height:
                patient_data.append(['Height', f"{submission.height} cm"])
            if submission.weight:
                patient_data.append(['Weight', f"{submission.weight} kg"])
            if submission.bmi:
                patient_data.append(['BMI', f"{submission.bmi}"])
            if submission.occupation:
                patient_data.append(['Occupation', submission.occupation])
            
            patient_table = Table(patient_data, colWidths=[2*inch, 4*inch])
            patient_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dbeafe')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(patient_table)
            elements.append(Spacer(1, 0.15*inch))
        
        # Symptoms
        symptoms = submission.submission_symptoms.all() if hasattr(submission, 'submission_symptoms') else []
        if symptoms:
            elements.append(Paragraph("<b>Reported Symptoms:</b>", self.styles['Normal']))
            symptom_data = [['Symptom', 'Severity', 'Duration', 'Onset']]
            for symptom in symptoms:
                symptom_data.append([
                    symptom.symptom.name if symptom.symptom else 'N/A',
                    f"{symptom.severity}/10" if symptom.severity else 'N/A',
                    symptom.duration or 'N/A',
                    symptom.get_onset_display() if symptom.onset else 'N/A'
                ])
            
            symptom_table = Table(symptom_data, colWidths=[2.5*inch, 1*inch, 1.5*inch, 1*inch])
            symptom_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fef3c7')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
            ]))
            elements.append(symptom_table)
            elements.append(Spacer(1, 0.15*inch))
        
        # Predictions
        predictions = submission.predicted_diseases.all() if hasattr(submission, 'predicted_diseases') else []
        if predictions:
            elements.append(Paragraph("<b>Predicted Conditions:</b>", self.styles['Normal']))
            pred_data = [['Rank', 'Disease', 'Confidence']]
            for pred in predictions:
                pred_data.append([
                    str(pred.rank) if pred.rank else 'N/A',
                    pred.disease.name if pred.disease else 'N/A',
                    f"{pred.confidence_score:.2f}%" if pred.confidence_score else 'N/A'
                ])
            
            pred_table = Table(pred_data, colWidths=[0.75*inch, 3.5*inch, 1.75*inch])
            pred_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ddd6fe')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
            ]))
            elements.append(pred_table)
            elements.append(Spacer(1, 0.15*inch))
        
        # Analysis Results
        analysis_data = [
            ['Analysis Results', ''],
            ['Primary Diagnosis', submission.primary_prediction.name if submission.primary_prediction else 'N/A'],
            ['Severity Score', f"{submission.severity_score}%" if submission.severity_score is not None else 'N/A'],
            ['Severity Category', submission.severity_category or 'N/A'],
        ]
        
        # Determine color based on severity
        severity_color = {
            'NORMAL': colors.HexColor('#d1fae5'),
            'MODERATE': colors.HexColor('#fef3c7'),
            'RISKY': colors.HexColor('#fee2e2')
        }.get(submission.severity_category, colors.white)
        
        analysis_table = Table(analysis_data, colWidths=[2*inch, 4*inch])
        analysis_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0e7ff')),
            ('BACKGROUND', (0, 3), (-1, 3), severity_color),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(analysis_table)
        
        # Recommendations
        if self.include_recommendations and submission.primary_prediction:
            elements.append(Spacer(1, 0.15*inch))
            self._add_recommendations(elements, submission.primary_prediction)

    def _add_recommendations(self, elements, disease):
        """Add recommendations section to PDF"""
        elements.append(Paragraph("<b>Recommendations:</b>", self.styles['Normal']))
        
        # Lifestyle Tips
        if disease.lifestyle_tips:
            elements.append(Paragraph("<i>Lifestyle Tips:</i>", self.styles['Normal']))
            tips = self._format_recommendations(disease.lifestyle_tips)
            for tip in tips[:5]:  # Limit to 5 tips
                elements.append(Paragraph(tip, self.styles['Normal']))
            elements.append(Spacer(1, 0.1*inch))
        
        # Diet Advice
        if disease.diet_advice:
            elements.append(Paragraph("<i>Diet Advice:</i>", self.styles['Normal']))
            advice = self._format_recommendations(disease.diet_advice)
            for item in advice[:5]:
                elements.append(Paragraph(item, self.styles['Normal']))
            elements.append(Spacer(1, 0.1*inch))
        
        # Medical Advice
        if disease.medical_advice:
            elements.append(Paragraph("<i>Medical Advice:</i>", self.styles['Normal']))
            medical = self._format_recommendations(disease.medical_advice)
            for item in medical[:5]:
                elements.append(Paragraph(item, self.styles['Normal']))

    def generate_csv(self):
        """Generate comprehensive CSV report"""
        output = StringIO()
        writer = csv.writer(output)
        
        # Headers
        headers = ['Date', 'Time', 'Primary Disease', 'Confidence', 'Severity Score', 'Severity Category']
        
        if self.include_personal:
            headers.extend(['Name', 'Age', 'Gender', 'Height (cm)', 'Weight (kg)', 'BMI', 'Occupation'])
        
        headers.extend(['Symptoms', 'Symptom Count', 'All Predictions'])
        
        if self.include_recommendations:
            headers.extend(['Lifestyle Tips', 'Diet Advice', 'Medical Advice'])
        
        writer.writerow(headers)
        
        # Data rows
        for submission in self.submissions:
            # Get primary prediction safely
            primary_disease = submission.primary_prediction.name if submission.primary_prediction else 'N/A'
            
            # Get first prediction confidence
            first_prediction = submission.predicted_diseases.first() if hasattr(submission, 'predicted_diseases') else None
            confidence = f"{first_prediction.confidence_score:.2f}" if first_prediction and first_prediction.confidence_score else "N/A"
            
            row = [
                submission.created_at.strftime('%Y-%m-%d'),
                submission.created_at.strftime('%H:%M:%S'),
                primary_disease,
                confidence,
                submission.severity_score if submission.severity_score is not None else 'N/A',
                submission.severity_category or 'N/A'
            ]
            
            if self.include_personal:
                row.extend([
                    submission.name or 'N/A',
                    submission.age if submission.age is not None else 'N/A',
                    submission.get_gender_display() if submission.gender else 'N/A',
                    submission.height if submission.height else '',
                    submission.weight if submission.weight else '',
                    submission.bmi if submission.bmi else '',
                    submission.occupation or ''
                ])
            
            # Symptoms
            symptoms = submission.submission_symptoms.all() if hasattr(submission, 'submission_symptoms') else []
            symptom_list = '; '.join([
                f"{s.symptom.name} (Severity: {s.severity}, Duration: {s.duration}, Onset: {s.get_onset_display()})"
                for s in symptoms if s.symptom
            ]) if symptoms else 'N/A'
            row.append(symptom_list)
            row.append(symptoms.count() if symptoms else 0)
            
            # All predictions
            predictions = submission.predicted_diseases.all() if hasattr(submission, 'predicted_diseases') else []
            pred_list = '; '.join([
                f"{p.disease.name} ({p.confidence_score:.2f}%)"
                for p in predictions if p.disease and p.confidence_score is not None
            ]) if predictions else 'N/A'
            row.append(pred_list)
            
            if self.include_recommendations and submission.primary_prediction:
                disease = submission.primary_prediction
                row.extend([
                    disease.lifestyle_tips.replace('\n', ' | ') if disease.lifestyle_tips else '',
                    disease.diet_advice.replace('\n', ' | ') if disease.diet_advice else '',
                    disease.medical_advice.replace('\n', ' | ') if disease.medical_advice else ''
                ])
            elif self.include_recommendations:
                row.extend(['', '', ''])
            
            writer.writerow(row)
        
        return output.getvalue()

    def generate_json(self):
        """Generate comprehensive JSON report"""
        data = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_predictions': self.submissions.count(),
                'date_range': {
                    'start': self.submissions.last().created_at.strftime('%Y-%m-%d'),
                    'end': self.submissions.first().created_at.strftime('%Y-%m-%d')
                },
                'include_personal_info': self.include_personal,
                'include_recommendations': self.include_recommendations
            },
            'predictions': []
        }
        
        for submission in self.submissions:
            submission_data = {
                'id': submission.id,
                'timestamp': submission.created_at.isoformat(),
                'date': submission.created_at.strftime('%Y-%m-%d'),
                'time': submission.created_at.strftime('%H:%M:%S'),
            }
            
            if self.include_personal:
                submission_data['personal_info'] = {
                    'name': submission.name or None,
                    'age': submission.age,
                    'gender': submission.get_gender_display() if submission.gender else None,
                    'height_cm': submission.height,
                    'weight_kg': submission.weight,
                    'bmi': submission.bmi,
                    'occupation': submission.occupation or None
                }
                
                # Medical history
                if submission.existing_diseases or submission.allergies or submission.medications:
                    submission_data['medical_history'] = {
                        'existing_diseases': submission.existing_diseases if submission.existing_diseases else [],
                        'allergies': submission.allergies or None,
                        'medications': submission.medications or None,
                        'family_history': submission.family_history or None
                    }
                
                # Lifestyle
                submission_data['lifestyle'] = {
                    'smoking': submission.smoking,
                    'alcohol': submission.alcohol,
                    'diet': submission.get_diet_display() if submission.diet else None,
                    'sleep_hours': submission.sleep_hours,
                    'exercise_frequency': submission.exercise_frequency or None,
                    'stress_level': submission.stress_level
                }
            
            # Symptoms
            symptoms = submission.submission_symptoms.all() if hasattr(submission, 'submission_symptoms') else []
            submission_data['symptoms'] = [
                {
                    'name': s.symptom.name if s.symptom else None,
                    'severity': s.severity,
                    'duration': s.duration or None,
                    'onset': s.get_onset_display() if s.onset else None
                }
                for s in symptoms
            ]
            
            # Predictions
            predictions = submission.predicted_diseases.all() if hasattr(submission, 'predicted_diseases') else []
            submission_data['predictions'] = [
                {
                    'rank': p.rank,
                    'disease': p.disease.name if p.disease else None,
                    'confidence_score': float(p.confidence_score) if p.confidence_score is not None else None
                }
                for p in predictions
            ]
            
            submission_data['analysis'] = {
                'primary_diagnosis': submission.primary_prediction.name if submission.primary_prediction else None,
                'severity_score': float(submission.severity_score) if submission.severity_score is not None else None,
                'severity_category': submission.severity_category or None
            }
            
            if self.include_recommendations and submission.primary_prediction:
                disease = submission.primary_prediction
                submission_data['recommendations'] = {
                    'lifestyle_tips': self._format_recommendations(disease.lifestyle_tips) if disease.lifestyle_tips else [],
                    'diet_advice': self._format_recommendations(disease.diet_advice) if disease.diet_advice else [],
                    'medical_advice': self._format_recommendations(disease.medical_advice) if disease.medical_advice else []
                }
            
            data['predictions'].append(submission_data)
        
        return json.dumps(data, indent=2)