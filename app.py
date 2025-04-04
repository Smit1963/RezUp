import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import io
import base64
import os
import re
import spacy
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.enums import TA_CENTER
import nltk
from nltk.corpus import stopwords
from collections import defaultdict

# Download NLTK data
nltk.download('stopwords')
nltk.download('punkt')

# Load environment variables
load_dotenv()

# Configure Google API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Load English language model for spaCy
try:
    nlp = spacy.load("en_core_web_lg")
except:
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_lg"])
    nlp = spacy.load("en_core_web_lg")

# ATS-specific rules and configurations
ATS_CONFIG = {
    "required_sections": ["experience", "education", "skills"],
    "section_order_preference": ["contact", "summary", "skills", "experience", "education"],
    "avoid_elements": ["tables", "images", "headers/footers"],
    "font_penalties": {
        "uncommon_fonts": -10,
        "size_variations": -5
    },
    "keyword_position_weights": {
        "summary": 1.5,
        "skills": 1.3,
        "experience": 1.2,
        "education": 1.0,
        "other": 0.8
    }
}

# Industry-specific keyword libraries (simplified example)
INDUSTRY_KEYWORDS = {
    "tech": ["python", "machine learning", "aws", "docker", "kubernetes"],
    "healthcare": ["patient care", "HIPAA", "EMR", "clinical", "CPR"],
    "finance": ["financial analysis", "Excel", "modeling", "GAAP", "forecasting"]
}

class ResumeAnalyzer:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.ats_keyword_db = self._load_ats_keywords()

    def _load_ats_keywords(self):
        """Load ATS keywords database (simplified example)"""
        return {
            "workday": ["achieved", "managed", "developed", "implemented"],
            "taleo": ["skills", "experience", "education", "certifications"],
            "greenhouse": ["collaborated", "led", "improved", "optimized"]
        }

    def parse_resume(self, text):
        """Parse resume text into structured data"""
        doc = nlp(text)

        # Extract entities
        entities = {
            "skills": [],
            "companies": [],
            "job_titles": [],
            "dates": [],
            "education": []
        }

        for ent in doc.ents:
            if ent.label_ == "ORG":
                entities["companies"].append(ent.text)
            elif ent.label_ == "DATE":
                entities["dates"].append(ent.text)

        # Simple section detection (would be more sophisticated in production)
        sections = {}
        current_section = None
        for line in text.split('\n'):
            line = line.strip()
            if line.endswith(':'):
                current_section = line[:-1].lower()
                sections[current_section] = []
            elif current_section:
                sections[current_section].append(line)

        return {
            "entities": entities,
            "sections": sections,
            "raw_text": text
        }

    def calculate_ats_score(self, resume_data, job_description):
        """Calculate comprehensive ATS score"""
        scores = {
            "keyword": self._keyword_score(resume_data, job_description),
            "section": self._section_score(resume_data),
            "format": self._format_score(resume_data),
            "experience": self._experience_match_score(resume_data, job_description)
        }

        # Weighted total score
        total_score = (
            scores["keyword"] * 0.4 +
            scores["section"] * 0.3 +
            scores["format"] * 0.2 +
            scores["experience"] * 0.1
        )

        return {
            "total_score": min(100, int(total_score * 100)),  # Convert to percentage
            "component_scores": scores,
            "missing_keywords": self._identify_missing_keywords(resume_data, job_description),
            "format_issues": self._identify_format_issues(resume_data)
        }

    def _keyword_score(self, resume_data, job_description):
        """Calculate keyword matching score"""
        # Extract keywords from job description
        job_keywords = self._extract_keywords(job_description)

        # Extract keywords from resume
        resume_keywords = defaultdict(int)
        for section, content in resume_data["sections"].items():
            section_text = ' '.join(content)
            keywords = self._extract_keywords(section_text)
            weight = ATS_CONFIG["keyword_position_weights"].get(section, 1.0)
            for kw in keywords:
                resume_keywords[kw] += weight

        # Calculate match
        matched = 0
        for kw in job_keywords:
            if kw in resume_keywords:
                matched += resume_keywords[kw]

        return matched / len(job_keywords) if job_keywords else 0

    def _section_score(self, resume_data):
        """Score based on resume sections"""
        score = 0
        present_sections = set(resume_data["sections"].keys())

        # Check required sections
        for req in ATS_CONFIG["required_sections"]:
            if req in present_sections:
                score += 0.3  # 30% of score for required sections

        # Check section order
        ideal_order = ATS_CONFIG["section_order_preference"]
        actual_order = [s for s in ideal_order if s in present_sections]
        if actual_order == ideal_order[:len(actual_order)]:
            score += 0.2  # 20% for proper order

        return score

    def _format_score(self, resume_data):
        """Score based on formatting"""
        # In a real app, this would analyze PDF structure
        # Here we just check for common issues in text
        text = resume_data["raw_text"].lower()
        penalties = 0

        # Check for tables
        if "table" in text:
            penalties += ATS_CONFIG["font_penalties"]["uncommon_fonts"]

        return max(0, 1 - (penalties / 100))

    def _experience_match_score(self, resume_data, job_description):
        """Score based on experience matching"""
        # Simple implementation - would use more sophisticated matching in production
        job_doc = nlp(job_description.lower())
        resume_doc = nlp(resume_data["raw_text"].lower())

        return job_doc.similarity(resume_doc)

    def _extract_keywords(self, text):
        """Extract keywords from text"""
        doc = nlp(text.lower())
        keywords = []

        for token in doc:
            if (token.is_alpha and not token.is_stop and
                    not token.is_punct and len(token.text) > 2):
                keywords.append(token.lemma_)

        return list(set(keywords))  # Remove duplicates

    def _identify_missing_keywords(self, resume_data, job_description):
        """Identify keywords missing from resume"""
        resume_keywords = set(self._extract_keywords(resume_data["raw_text"]))
        job_keywords = set(self._extract_keywords(job_description))

        return list(job_keywords - resume_keywords)

    def _identify_format_issues(self, resume_data):
        """Identify potential formatting issues"""
        issues = []
        text = resume_data["raw_text"].lower()

        if "table" in text:
            issues.append("Avoid using tables - may not parse correctly in ATS")

        return issues

# Initialize analyzer
analyzer = ResumeAnalyzer()

def get_gemini_response(input_text, pdf_content, prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([input_text, pdf_content[0], prompt])
    return response.text

def convert_pdf_to_image(uploaded_file):
    pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    page = pdf_document.load_page(0)  # Load the first page
    pix = page.get_pixmap()

    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()

    pdf_parts = [
        {
            "mime_type": "image/jpeg",
            "data": base64.b64encode(img_byte_arr).decode()
        }
    ]
    return pdf_parts

def extract_text_from_pdf(uploaded_file):
    """Extract text from PDF using PyMuPDF"""
    pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in pdf_document:
        text += page.get_text()
    return text

def generate_improved_resume(resume_text, job_description, analysis_results):
    prompt = f"""
    Based on the job description and current resume analysis, generate an improved resume that:
    1. Incorporates these missing keywords: {analysis_results['missing_keywords']}
    2. Addresses these format issues: {analysis_results['format_issues']}
    3. Scores {analysis_results['total_score']}% but should score at least 85%
    4. Follows ATS best practices:
        - Uses standard section headers
        - Avoids tables and graphics
        - Uses common fonts
        - Includes quantifiable achievements

    Job Description: {job_description}

    Current Resume: {resume_text}

    Generate the improved resume with these sections:
    - Header (Name, Contact Info)
    - Professional Summary (tailored to job)
    - Skills (categorized and matching job)
    - Work Experience (with quantifiable achievements)
    - Education
    - Certifications (if relevant)

    Make the resume ATS-optimized while keeping it human-friendly.
    """
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text

def create_pdf(resume_text):
    """Create PDF using ReportLab with proper style handling"""
    buffer = io.BytesIO()
    styles = getSampleStyleSheet()

    # Modify existing BodyText style
    body_style = styles['BodyText']
    body_style.spaceAfter = 6

    # Add custom styles
    if 'RezUpSectionHeader' not in styles:
        styles.add(ParagraphStyle(
            name='RezUpSectionHeader',
            fontName='Helvetica-Bold',
            fontSize=14,
            spaceAfter=12
        ))

    if 'RezUpCenter' not in styles:
        styles.add(ParagraphStyle(
            name='RezUpCenter',
            alignment=TA_CENTER
        ))

    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []

    # Add title
    story.append(Paragraph("Optimized Resume", styles['Title']))
    story.append(Spacer(1, 24))

    # Process content
    for line in resume_text.split('\n'):
        if not line.strip():
            story.append(Spacer(1, 12))
            continue

        if line.strip().endswith(':'):  # Section header
            story.append(Paragraph(line, styles['RezUpSectionHeader']))
        else:
            story.append(Paragraph(line, body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

# Streamlit UI Setup
st.set_page_config(page_title="RezUp Pro - Advanced Resume Optimizer", layout="wide")

# Custom CSS styling (same as before)
st.markdown("""
    <style>
        /* Previous CSS styles here */
        .score-details {
            background-color: #f5f5f5;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }
        .keyword-chip {
            display: inline-block;
            background-color: #e3f2fd;
            padding: 4px 8px;
            border-radius: 16px;
            margin: 4px;
            font-size: 14px;
        }
        .missing-keyword {
            background-color: #ffebee;
        }
    </style>
""", unsafe_allow_html=True)

# App Header
st.markdown('<h1 class="main-title">☄️RezUp Pro</h1>', unsafe_allow_html=True)
st.markdown('<p class="tagline">Advanced ATS Resume Optimization</p>', unsafe_allow_html=True)

# Main Content
with st.container():
    st.markdown('<div class="centered">', unsafe_allow_html=True)
    input_text = st.text_area("📝 Enter Job Description", key="input",
                                    placeholder="Paste the job description you're applying for...")
    uploaded_file = st.file_uploader("📂 Upload Your Resume (PDF only)", type="pdf", key="file")
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_file is not None:
        st.markdown('<p class="success-message">✅ Resume uploaded successfully!</p>', unsafe_allow_html=True)

# Action Buttons
st.markdown('<div class="action-buttons">', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)
with col1:
    submit_1 = st.button("🔍 Resume Evaluation", key="eval")
with col2:
    submit_2 = st.button("💡 Skillset Improvement", key="skills")
with col3:
    submit_3 = st.button("🔑 Missing Keywords", key="keywords")
with col4:
    submit_4 = st.button("📊 ATS Score", key="score")
st.markdown('</div>', unsafe_allow_html=True)

# Generate Button
st.markdown('<div class="generate-btn-container">', unsafe_allow_html=True)
generate_clicked = st.button("✨ Generate Improved Resume", key="generate")
st.markdown('</div>', unsafe_allow_html=True)

# Button Handlers
if submit_1 or submit_2 or submit_3 or submit_4 or generate_clicked:
    if uploaded_file is not None and input_text:
        # Extract and analyze resume
        resume_text = extract_text_from_pdf(uploaded_file)
        resume_data = analyzer.parse_resume(resume_text)
        analysis_results = analyzer.calculate_ats_score(resume_data, input_text)

        if submit_1:  # Resume Evaluation
            with st.spinner("🔍 Analyzing your resume..."):
                st.markdown('<h2 class="sub-header">🔍 Professional Evaluation</h2>', unsafe_allow_html=True)

                # Display score
                st.markdown(f"""
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {analysis_results['total_score']}%"></div>
                    </div>
                    <p style="text-align: center; font-weight: bold;">Current ATS Match: {analysis_results['total_score']}%</p>
                """, unsafe_allow_html=True)

                # Detailed evaluation
                evaluation_prompt = f"""
                    As an experienced HR professional, provide a detailed evaluation of this resume against the job description.

                    Current ATS Score: {analysis_results['total_score']}%
                    Missing Keywords: {analysis_results['missing_keywords']}
                    Format Issues: {analysis_results['format_issues']}

                    Provide analysis in this format:

                    ### Strengths:
                    - List key strengths

                    ### Weaknesses:
                    - List areas needing improvement
                    """

                evaluation = get_gemini_response(input_text,
                                                 [{"mime_type": "text/plain", "data": base64.b64encode(resume_text.encode()).decode()}],
                                                 evaluation_prompt)
                st.markdown(f'<div class="response-container">{evaluation}</div>', unsafe_allow_html=True)

        elif submit_2:  # Skillset Improvement
            with st.spinner("💡 Generating improvement suggestions..."):
                st.markdown('<h2 class="sub-header">💡 Skillset Development Plan</h2>', unsafe_allow_html=True)

                skills_prompt = f"""
                    Analyze this resume and job description to create a skills development plan:

                    Resume Skills: {resume_data['entities']['skills']}
                    Job Requirements: {analyzer._extract_keywords(input_text)}
                    Missing Keywords: {analysis_results['missing_keywords']}

                    Provide:
                    1. Skills gap analysis
                    2. Recommended learning resources
                    3. Timeline for improvement
                    """

                skills_analysis = get_gemini_response(input_text,
                                                     [{"mime_type": "text/plain", "data": base64.b64encode(resume_text.encode()).decode()}],
                                                     skills_prompt)
                st.markdown(f'<div class="response-container">{skills_analysis}</div>', unsafe_allow_html=True)

        elif submit_3:  # Missing Keywords
            with st.spinner("🔍 Scanning for missing keywords..."):
                st.markdown('<h2 class="sub-header">🔑 Critical Missing Keywords</h2>', unsafe_allow_html=True)

                # Display missing keywords
                st.markdown("<h3>Missing Keywords from Job Description:</h3>", unsafe_allow_html=True)
                for kw in analysis_results['missing_keywords']:
                    st.markdown(f'<span class="keyword-chip missing-keyword">{kw}</span>', unsafe_allow_html=True)

                # Show keyword analysis
                st.markdown("<h3 style='margin-top: 20px;'>Keyword Analysis:</h3>", unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="score-details">
                        <p><strong>Keyword Match Score:</strong> {int(analysis_results['component_scores']['keyword'] * 100)}%</p>
                        <p>This measures how well your resume includes important keywords from the job description.</p>
                    </div>
                """, unsafe_allow_html=True)

        elif submit_4:  # ATS Score
            with st.spinner("📊 Calculating ATS score..."):
                st.markdown('<h2 class="sub-header">📊 ATS Compatibility Report</h2>', unsafe_allow_html=True)

                # Display comprehensive score breakdown
                st.markdown(f"""
                    <div class="score-comparison">
                        <div class="score-box {'optimized-score' if analysis_results['total_score'] > 70 else 'original-score'}">
                            <h3>ATS Compatibility Score</h3>
                            <div class="score-value">{analysis_results['total_score']}%</div>
                            <p>{'Good' if analysis_results['total_score'] > 70 else 'Needs Improvement'}</p>
                        </div>
                    </div>

                    <h3>Score Breakdown:</h3>
                    <div class="score-details">
                        <p><strong>Keyword Matching:</strong> {int(analysis_results['component_scores']['keyword'] * 100)}%</p>
                        <p><strong>Section Completeness:</strong> {int(analysis_results['component_scores']['section'] * 100)}%</p>
                        <p><strong>Formatting:</strong> {int(analysis_results['component_scores']['format'] * 100)}%</p>
                        <p><strong>Experience Relevance:</strong> {int(analysis_results['component_scores']['experience'] * 100)}%</p>
                    </div>

                    <h3>Formatting Issues:</h3>
                    <ul>
                        {''.join([f'<li>{issue}</li>' for issue in analysis_results['format_issues']]) or '<li>No major formatting issues detected</li>'}
                    </ul>
                """, unsafe_allow_html=True)

        elif generate_clicked:  # Generate Improved Resume
            with st.spinner("✨ Creating your optimized resume..."):
                # Generate improved resume
                improved_resume = generate_improved_resume(resume_text, input_text, analysis_results)

                # Analyze the improved version
                improved_data = analyzer.parse_resume(improved_resume)
                improved_analysis = analyzer.calculate_ats_score(improved_data, input_text)

                # Display results
                st.markdown('<h2 class="sub-header">✨ Optimization Results</h2>', unsafe_allow_html=True)

                # Score comparison
                st.markdown(f"""
                    <div class="score-comparison">
                        <div class="score-box original-score">
                            <h3>Original Score</h3>
                            <div class="score-value">{analysis_results['total_score']}%</div>
                        </div>
                        <div class="score-box optimized-score">
                            <h3>Optimized Score</h3>
                            <div class="score-value">{improved_analysis['total_score']}%</div>
                        </div>
                    </div>

                    <div style="text-align: center; margin: 20px 0;">
                        <h3>Improvement: {improved_analysis['total_score'] - analysis_results['total_score']}% increase</h3>
                    </div>
                """, unsafe_allow_html=True)

                # Show improved resume
                with st.expander("🆕 View Optimized Resume"):
                    st.markdown(f'<div class="response-container">{improved_resume}</div>', unsafe_allow_html=True)

                # The following section for displaying "Key Improvements Made" is removed
                # st.markdown('<h3>Key Improvements Made:</h3>', unsafe_allow_html=True)
                # changes_prompt = f"""
                #     Compare these two resumes and list the key improvements made:

                #     Original Resume (Score: {analysis_results['total_score']}%):
                #     {resume_text}

                #     Optimized Resume (Score: {improved_analysis['total_score']}%):
                #     {improved_resume}

                #     List the specific changes that improved the ATS score in bullet points.
                #     """

                # changes = get_gemini_response("",
                #                               [{"mime_type": "text/plain", "data": base64.b64encode(changes_prompt.encode()).decode()}],
                #                               changes_prompt)
                # st.markdown(f'<div class="response-container">{changes}</div>', unsafe_allow_html=True)

                # Download button
                try:
                    pdf_buffer = create_pdf(improved_resume)
                    st.download_button(
                        label="📄 Download Improved Resume (PDF)",
                        data=pdf_buffer,
                        file_name="optimized_resume.pdf",
                        mime="application/pdf",
                        key="download-resume",
                        type="primary",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error generating PDF: {str(e)}")

    elif not input_text:
        st.warning("Please enter a job description to analyze your resume")
    else:
        st.warning("Please upload your resume to proceed")
