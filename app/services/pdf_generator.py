import io
from datetime import datetime
from typing import List, Any
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, grey
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

from app.schemas.recommendation import RecommendationResponse, CourseMatch


class PDFGenerator:
    """
    Service for generating PDF reports of course recommendations.
    Creates professional-looking documents with course details and match explanations.
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Set up custom styles for the PDF document."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=HexColor('#1f2937'),
            alignment=TA_CENTER
        ))
        
        # Heading style
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=HexColor('#374151'),
            borderWidth=1,
            borderColor=HexColor('#e5e7eb'),
            borderPadding=8
        ))
        
        # Course title style
        self.styles.add(ParagraphStyle(
            name='CourseTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=6,
            spaceBefore=12,
            textColor=HexColor('#1f2937'),
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            textColor=HexColor('#6b7280'),
            fontName='Helvetica-Oblique'
        ))
        
        # Match score style
        self.styles.add(ParagraphStyle(
            name='MatchScore',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=6,
            textColor=HexColor('#059669'),
            fontName='Helvetica-Bold'
        ))
    
    def generate_recommendations_pdf(self, recommendations: RecommendationResponse, 
                                   user_query: dict = None) -> bytes:
        """
        Generate a PDF report for course recommendations.
        
        Args:
            recommendations: The recommendation response data
            user_query: Original user query parameters (optional)
            
        Returns:
            PDF content as bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build the story (content)
        story = []
        
        # Title page
        story.extend(self._create_title_page(recommendations, user_query))
        
        # Summary section
        story.extend(self._create_summary_section(recommendations))
        
        # Recommendations section
        story.extend(self._create_recommendations_section(recommendations.recommendations))
        
        # Appendix with search metadata
        story.extend(self._create_appendix_section(recommendations))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
    
    def _create_title_page(self, recommendations: RecommendationResponse, 
                          user_query: dict = None) -> List[Any]:
        """Create the title page of the PDF."""
        story = []
        
        # Main title
        title = Paragraph("CourseMatch Recommendations", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.5 * inch))
        
        # Subtitle with date
        date_str = datetime.now().strftime("%B %d, %Y")
        subtitle = Paragraph(f"Personalized Course Recommendations<br/>{date_str}", 
                           self.styles['Subtitle'])
        story.append(subtitle)
        story.append(Spacer(1, 0.5 * inch))
        
        # User query summary (if provided)
        if user_query:
            story.append(Paragraph("Search Criteria", self.styles['CustomHeading']))
            query_info = self._format_user_query(user_query)
            story.append(Paragraph(query_info, self.styles['Normal']))
            story.append(Spacer(1, 0.3 * inch))
        
        # Summary stats
        stats_data = [
            ["Total Matches Found", str(recommendations.total_matches)],
            ["Top Recommendations", str(len(recommendations.recommendations))],
            ["Analysis Date", date_str]
        ]
        
        stats_table = Table(stats_data, colWidths=[3 * inch, 2 * inch])
        stats_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f9fafb')),
        ]))
        
        story.append(stats_table)
        story.append(PageBreak())
        
        return story
    
    def _create_summary_section(self, recommendations: RecommendationResponse) -> List[Any]:
        """Create the summary section."""
        story = []
        
        story.append(Paragraph("Executive Summary", self.styles['CustomHeading']))
        
        # Overview paragraph
        summary_text = f"""
        This report presents {len(recommendations.recommendations)} carefully selected course 
        recommendations from a total of {recommendations.total_matches} matching programs. 
        Each recommendation includes detailed match analysis, skill alignment, and practical 
        considerations to help you make an informed decision.
        """
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))
        
        # Key insights
        if recommendations.suggestions:
            story.append(Paragraph("Key Insights & Suggestions", self.styles['Heading2']))
            for suggestion in recommendations.suggestions:
                bullet_text = f"• {suggestion}"
                story.append(Paragraph(bullet_text, self.styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))
        
        return story
    
    def _create_recommendations_section(self, recommendations: List[CourseMatch]) -> List[Any]:
        """Create the detailed recommendations section."""
        story = []
        
        story.append(Paragraph("Course Recommendations", self.styles['CustomHeading']))
        
        for i, course_match in enumerate(recommendations, 1):
            story.extend(self._create_course_detail(course_match, i))
            
            # Add page break after every 2 courses (except the last one)
            if i % 2 == 0 and i < len(recommendations):
                story.append(PageBreak())
        
        return story
    
    def _create_course_detail(self, course_match: CourseMatch, rank: int) -> List[Any]:
        """Create detailed section for a single course recommendation."""
        story = []
        course = course_match.course
        
        # Course header
        header_text = f"{rank}. {course.name}"
        story.append(Paragraph(header_text, self.styles['CourseTitle']))
        
        # Institution and basic info
        institution_text = f"{course.institution}"
        if course.location_city and course.location_country:
            institution_text += f" • {course.location_city}, {course.location_country}"
        if course.modality:
            institution_text += f" • {course.modality.title()}"
        
        story.append(Paragraph(institution_text, self.styles['Subtitle']))
        
        # Match score
        score_text = f"Match Score: {course_match.match_score:.1%}"
        story.append(Paragraph(score_text, self.styles['MatchScore']))
        
        # Match explanation
        story.append(Paragraph("Why This Course Matches:", self.styles['Heading3']))
        story.append(Paragraph(course_match.match_explanation, self.styles['Normal']))
        
        # Course details table
        details_data = []
        
        if course.duration_months:
            details_data.append(["Duration", f"{course.duration_months} months"])
        
        if course.tuition_fee:
            fee_text = f"{course.currency or 'USD'} {course.tuition_fee:,.0f}"
            details_data.append(["Tuition Fee", fee_text])
        
        if course.course_level:
            details_data.append(["Level", course.course_level.title()])
        
        if course.language_of_instruction:
            details_data.append(["Language", course.language_of_instruction])
        
        if course.application_deadline:
            deadline_str = course.application_deadline.strftime("%B %d, %Y")
            details_data.append(["Application Deadline", deadline_str])
        
        if details_data:
            details_table = Table(details_data, colWidths=[1.5 * inch, 3 * inch])
            details_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
                ('BACKGROUND', (0, 0), (0, -1), HexColor('#f9fafb')),
            ]))
            story.append(details_table)
        
        # Skills and outcomes
        if course_match.skill_matches:
            story.append(Paragraph("Matching Skills:", self.styles['Heading3']))
            skills_text = " • ".join(course_match.skill_matches)
            story.append(Paragraph(skills_text, self.styles['Normal']))
        
        # Course description
        if course.description:
            story.append(Paragraph("Course Description:", self.styles['Heading3']))
            # Truncate long descriptions
            description = course.description[:500] + "..." if len(course.description) > 500 else course.description
            story.append(Paragraph(description, self.styles['Normal']))
        
        story.append(Spacer(1, 0.3 * inch))
        
        return story
    
    def _create_appendix_section(self, recommendations: RecommendationResponse) -> List[Any]:
        """Create appendix with technical details."""
        story = []
        
        story.append(PageBreak())
        story.append(Paragraph("Appendix: Search Analysis", self.styles['CustomHeading']))
        
        # Search metadata
        if recommendations.search_metadata:
            metadata = recommendations.search_metadata
            
            metadata_data = []
            for key, value in metadata.items():
                if isinstance(value, dict):
                    value_str = ", ".join([f"{k}: {v}" for k, v in value.items()])
                else:
                    value_str = str(value)
                metadata_data.append([key.replace("_", " ").title(), value_str])
            
            if metadata_data:
                metadata_table = Table(metadata_data, colWidths=[2 * inch, 3.5 * inch])
                metadata_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
                    ('BACKGROUND', (0, 0), (0, -1), HexColor('#f9fafb')),
                ]))
                story.append(metadata_table)
        
        # Disclaimer
        disclaimer_text = """
        Disclaimer: This report is generated based on available course data and automated 
        matching algorithms. Course details, fees, and requirements may change. Please verify 
        all information directly with the institutions before making decisions.
        """
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("Important Notice", self.styles['Heading3']))
        story.append(Paragraph(disclaimer_text, self.styles['Normal']))
        
        return story
    
    def _format_user_query(self, user_query: dict) -> str:
        """Format user query parameters for display."""
        formatted_parts = []
        
        if user_query.get('skills'):
            skills_str = ", ".join(user_query['skills'])
            formatted_parts.append(f"<b>Skills:</b> {skills_str}")
        
        if user_query.get('interests'):
            interests_str = ", ".join(user_query['interests'])
            formatted_parts.append(f"<b>Interests:</b> {interests_str}")
        
        if user_query.get('location'):
            formatted_parts.append(f"<b>Location:</b> {user_query['location']}")
        
        if user_query.get('career_goals'):
            formatted_parts.append(f"<b>Career Goals:</b> {user_query['career_goals']}")
        
        if user_query.get('modality'):
            formatted_parts.append(f"<b>Modality:</b> {user_query['modality']}")
        
        if user_query.get('max_tuition'):
            formatted_parts.append(f"<b>Max Tuition:</b> ${user_query['max_tuition']:,.0f}")
        
        return "<br/>".join(formatted_parts) if formatted_parts else "No specific criteria provided"