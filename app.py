import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import io
import base64
import os
import re
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.enums import TA_CENTER

# Load environment variables
load_dotenv()

# Configure Google API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

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

def generate_improved_resume(input_text, pdf_content):
    prompt = """
    Based on the job description and current resume, generate an improved resume that:
    1. Incorporates all missing keywords and skills from the job description
    2. Maintains the original structure but enhances content with quantifiable achievements
    3. Optimizes for ATS systems with proper keyword placement
    4. Presents information clearly and professionally
    5. Uses active language and power verbs
    6. Ensures consistent formatting throughout
    
    Format the resume with these sections:
    - Header (Name, Contact Info, LinkedIn)
    - Professional Summary (tailored to the job)
    - Technical Skills (categorized and matching job requirements)
    - Work Experience (with quantified achievements using numbers/percentages)
    - Education
    - Certifications (if any)
    - Projects (if relevant)
    
    Make sure the content is concise, achievement-oriented, and perfectly tailored to the job description.
    Include specific keywords from the job description naturally in context.
    """
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([input_text, pdf_content[0], prompt])
    return response.text

def create_pdf(resume_text):
    """Create PDF using ReportLab with proper style handling"""
    buffer = io.BytesIO()
    styles = getSampleStyleSheet()
    
    # Add custom styles
    styles.add(ParagraphStyle(
        name='RezUpHeader',
        fontName='Helvetica-Bold',
        fontSize=16,
        spaceAfter=12
    ))
    
    styles.add(ParagraphStyle(
        name='RezUpSubheader',
        fontName='Helvetica-Bold',
        fontSize=14,
        spaceAfter=8
    ))
    
    styles.add(ParagraphStyle(
        name='RezUpBody',
        fontSize=12,
        leading=14,
        spaceAfter=6
    ))
    
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    
    # Process content
    for line in resume_text.split('\n'):
        if not line.strip():
            story.append(Spacer(1, 12))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:], styles['RezUpHeader']))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:], styles['RezUpSubheader']))
        elif line.startswith('**') and line.endswith('**'):
            story.append(Paragraph(line[2:-2], styles['Heading3']))
        else:
            story.append(Paragraph(line, styles['RezUpBody']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def extract_score_from_evaluation(evaluation_text):
    """Extract the percentage score from evaluation text"""
    match = re.search(r'(\d{1,3})%', evaluation_text)
    return int(match.group(1)) if match else 0

def extract_missing_keywords(evaluation_text):
    """Extract missing keywords from evaluation text"""
    lines = evaluation_text.split('\n')
    keywords = []
    in_section = False
    for line in lines:
        if "missing keywords" in line.lower():
            in_section = True
        elif in_section and line.strip().startswith('-'):
            keywords.append(line.strip()[1:].strip())
        elif in_section and not line.strip():
            break
    return keywords

def evaluate_resume_progress(original_score, optimized_score, original_missing, optimized_missing):
    """Generate a progress report showing improvements"""
    improvement = optimized_score - original_score
    recovered_keywords = set(original_missing) - set(optimized_missing)
    
    recommendations = [
        "More targeted keyword integration",
        "Better achievement quantification",
        "Improved section organization"
    ] if improvement <= 5 else ["Great improvement! Maintain these changes"]
    
    return f"""
## ATS Optimization Progress Report

**Original Score**: {original_score}%  
**Optimized Score**: {optimized_score}%  
**Improvement**: {improvement}%  

### Key Improvements:
- Recovered {len(recovered_keywords)} keywords: {', '.join(recovered_keywords) if recovered_keywords else 'None'}
- Improved formatting for better ATS parsing  
- Enhanced keyword placement and frequency  

### Recommendations:
{'- ' + '\n- '.join(recommendations)}
"""

# Streamlit UI Setup
st.set_page_config(page_title="RezUp - Resume Optimizer", layout="wide", page_icon="logo.png")

# Custom CSS styling
st.markdown("""
    <style>
        /* [Keep all your original CSS exactly the same] */
    </style>
""", unsafe_allow_html=True)

# App Header
st.markdown('<h1 class="main-title">☄️RezUp! Till You Make It</h1>', unsafe_allow_html=True)
st.markdown('<p class="tagline">AI that fixes your resume</p>', unsafe_allow_html=True)

# Main Content
with st.container():
    st.markdown('<div class="centered">', unsafe_allow_html=True)
    input_text = st.text_area("📝 Enter Job Description", key="input", 
                             placeholder="Paste the job description you're applying for...")
    uploaded_file = st.file_uploader("📂 Upload Your Resume (PDF only)", type="pdf", key="file")
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_file is not None:
        st.markdown('<p class="success-message">✅ Resume uploaded successfully!</p>', unsafe_allow_html=True)

# Initialize session state
if 'generate_clicked' not in st.session_state:
    st.session_state.generate_clicked = False

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
if st.button("✨ Generate Improved Resume", key="generate"):
    st.session_state.generate_clicked = True

# Prompts (keep your original prompts exactly the same)

# Button Handlers
if submit_1:
    if uploaded_file is not None:
        with st.spinner("🔍 Analyzing your resume..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            response = get_gemini_response(input_text, pdf_content, input_prompt1)
            st.markdown('<h2 class="sub-header">🔍 Professional Evaluation</h2>', unsafe_allow_html=True)
            
            score = extract_score_from_evaluation(response)
            st.markdown(f"""
            <div class="progress-bar">
                <div class="progress-fill" style="width: {score}%"></div>
            </div>
            <p style="text-align: center; font-weight: bold;">Current Match: {score}%</p>
            """, unsafe_allow_html=True)
            
            st.markdown(f'<div class="response-container">{response}</div>', unsafe_allow_html=True)
    else:
        st.warning("Please upload your resume to get analysis")

elif submit_2:
    if uploaded_file is not None:
        with st.spinner("💡 Generating improvement suggestions..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            response = get_gemini_response(input_text, pdf_content, input_prompt2)
            st.markdown('<h2 class="sub-header">💡 Skillset Development Plan</h2>', unsafe_allow_html=True)
            st.markdown(f'<div class="response-container">{response}</div>', unsafe_allow_html=True)
    else:
        st.warning("Please upload your resume to get suggestions")

elif submit_3:
    if uploaded_file is not None:
        with st.spinner("🔍 Scanning for missing keywords..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            response = get_gemini_response(input_text, pdf_content, input_prompt4)
            st.markdown('<h2 class="sub-header">🔑 Critical Missing Keywords</h2>', unsafe_allow_html=True)
            
            score = extract_score_from_evaluation(response)
            st.markdown(f"""
            <div class="progress-bar">
                <div class="progress-fill" style="width: {score}%"></div>
            </div>
            <p style="text-align: center; font-weight: bold;">Current ATS Match: {score}%</p>
            """, unsafe_allow_html=True)
            
            st.markdown(f'<div class="response-container">{response}</div>', unsafe_allow_html=True)
    else:
        st.warning("Please upload your resume to check keywords")

elif submit_4:
    if uploaded_file is not None:
        with st.spinner("📊 Calculating ATS score..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            response = get_gemini_response(input_text, pdf_content, input_prompt3)
            st.markdown('<h2 class="sub-header">📊 ATS Compatibility Report</h2>', unsafe_allow_html=True)
            
            score = extract_score_from_evaluation(response)
            st.markdown(f"""
            <div class="progress-bar">
                <div class="progress-fill" style="width: {score}%"></div>
            </div>
            <p style="text-align: center; font-weight: bold;">Current ATS Score: {score}%</p>
            """, unsafe_allow_html=True)
            
            st.markdown(f'<div class="response-container">{response}</div>', unsafe_allow_html=True)
    else:
        st.warning("Please upload your resume to get ATS score")

if st.session_state.generate_clicked:
    if uploaded_file is not None and input_text:
        with st.spinner("✨ Creating your optimized resume..."):
            # First get original evaluation
            pdf_content = convert_pdf_to_image(uploaded_file)
            original_evaluation = get_gemini_response(input_text, pdf_content, input_prompt3)
            original_score = extract_score_from_evaluation(original_evaluation)
            original_missing = extract_missing_keywords(original_evaluation)
            
            # Generate improved resume
            improved_resume = generate_improved_resume(input_text, pdf_content)
            
            # Evaluate improved version
            improved_content = [{"mime_type": "text/plain", "data": base64.b64encode(improved_resume.encode()).decode()}]
            improved_evaluation = get_gemini_response(input_text, improved_content, input_prompt3)
            improved_score = extract_score_from_evaluation(improved_evaluation)
            improved_missing = extract_missing_keywords(improved_evaluation)
            
            # Generate comparison report
            progress_report = evaluate_resume_progress(original_score, improved_score, 
                                                    original_missing, improved_missing)
            
            # Display results
            st.markdown('<h2 class="sub-header">✨ Optimization Results</h2>', unsafe_allow_html=True)
            
            # Score comparison visualization
            st.markdown(f"""
            <div class="score-comparison">
                <div class="score-box original-score">
                    <h3>Original Score</h3>
                    <div class="score-value">{original_score}%</div>
                </div>
                <div class="score-box optimized-score">
                    <h3>Optimized Score</h3>
                    <div class="score-value">{improved_score}%</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Improvement percentage
            improvement = improved_score - original_score
            st.markdown(f"""
            <div style="text-align: center; margin: 20px 0;">
                <h3>Improvement: {improvement}% increase</h3>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("📝 Original Resume Evaluation"):
                st.markdown(f'<div class="response-container">{original_evaluation}</div>', unsafe_allow_html=True)
            
            with st.expander("🆕 Optimized Resume"):
                st.markdown(f'<div class="response-container">{improved_resume}</div>', unsafe_allow_html=True)
            
            with st.expander("🔍 Optimized Resume Evaluation"):
                st.markdown(f'<div class="response-container">{improved_evaluation}</div>', unsafe_allow_html=True)
            
            st.markdown('<h3 class="sub-header">📈 Improvement Report</h3>', unsafe_allow_html=True)
            st.markdown(f'<div class="response-container">{progress_report}</div>', unsafe_allow_html=True)
            
            # Download button
            try:
                pdf_buffer = create_pdf(improved_resume)
                st.download_button(
                    label="📄 Download Improved Resume (PDF)",
                    data=pdf_buffer,
                    file_name="improved_resume.pdf",
                    mime="application/pdf",
                    key="download-resume",
                    type="primary",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")
    elif not input_text:
        st.warning("Please enter a job description to optimize your resume")
    else:
        st.warning("Please upload your resume to generate an improved version")
    
    # Reset the generate click state
    st.session_state.generate_clicked = False
