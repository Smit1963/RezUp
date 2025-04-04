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
    
    # Modify existing BodyText style instead of redefining
    body_style = styles['BodyText']
    body_style.spaceAfter = 6
    
    # Add custom styles with unique names
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
    story.append(Paragraph("Improved Resume", styles['Title']))
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
        "Add more quantifiable achievements (numbers, percentages)",
        "Include missing keywords naturally in context",
        "Ensure consistent formatting throughout",
        "Optimize section headers for ATS parsing"
    ]
    
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
- {recommendations[0]}
- {recommendations[1]}
- {recommendations[2]}
- {recommendations[3]}
"""

# Streamlit UI Setup
st.set_page_config(page_title="RezUp - Resume Optimizer", layout="wide")

# Custom CSS styling
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
        
        :root {
            --primary: #4CAF50;
            --secondary: #2196F3;
            --accent: #FF5722;
            --dark: #333333;
        }
        
        html, body, [class*="css"] {
            font-family: 'Poppins', sans-serif;
        }
        
        .main-title {
            color: var(--primary);
            font-size: 2.5rem;
            text-align: center;
            margin-bottom: 0.5rem;
        }
        
        .stButton button {
            background-color: var(--primary);
            color: white;
            border-radius: 8px;
        }
        
        .stButton button:hover {
            background-color: var(--secondary);
        }
        
        .response-container {
            background-color: #f9f9f9;
            padding: 1rem;
            border-radius: 8px;
            margin-top: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

# App Header
st.markdown('<h1 class="main-title">RezUp - Resume Optimizer</h1>', unsafe_allow_html=True)

# Main Content
input_text = st.text_area("📝 Enter Job Description", placeholder="Paste the job description here...")
uploaded_file = st.file_uploader("📂 Upload Your Resume (PDF only)", type="pdf")

if uploaded_file is not None:
    st.success("✅ Resume uploaded successfully!")

# Action Buttons
col1, col2, col3, col4 = st.columns(4)
with col1:
    submit_1 = st.button("🔍 Resume Evaluation")
with col2:
    submit_2 = st.button("💡 Skillset Improvement")
with col3:
    submit_3 = st.button("🔑 Missing Keywords")
with col4:
    submit_4 = st.button("📊 ATS Score")

generate_clicked = st.button("✨ Generate Improved Resume", type="primary")

# Prompts
input_prompt1 = """
As an experienced HR manager, review this resume against the job description. 
Provide a professional evaluation including:
1. Percentage match score at the top
2. Key strengths matching job requirements
3. Potential weaknesses or gaps
4. Overall suitability for the position
"""

input_prompt3 = """
As an ATS optimization expert, evaluate this resume for:
1. Percentage match with job description
2. Present keywords (with frequency)
3. Missing keywords
4. Formatting issues affecting ATS parsing
5. Specific recommendations for improvement
"""

# Button Handlers
if submit_1 and uploaded_file:
    with st.spinner("Analyzing your resume..."):
        pdf_content = convert_pdf_to_image(uploaded_file)
        response = get_gemini_response(input_text, pdf_content, input_prompt1)
        st.subheader("🔍 Professional Evaluation")
        st.markdown(f'<div class="response-container">{response}</div>', unsafe_allow_html=True)

elif submit_3 and uploaded_file:
    with st.spinner("Scanning for missing keywords..."):
        pdf_content = convert_pdf_to_image(uploaded_file)
        response = get_gemini_response(input_text, pdf_content, input_prompt3)
        st.subheader("🔑 ATS Keyword Analysis")
        st.markdown(f'<div class="response-container">{response}</div>', unsafe_allow_html=True)

if generate_clicked and uploaded_file and input_text:
    with st.spinner("Creating your optimized resume..."):
        # Get original evaluation
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
        progress_report = evaluate_resume_progress(
            original_score, improved_score, 
            original_missing, improved_missing
        )
        
        # Display results
        st.subheader("✨ Optimization Results")
        st.markdown(progress_report)
        
        with st.expander("View Optimized Resume"):
            st.markdown(improved_resume)
        
        # Download button
        try:
            pdf_buffer = create_pdf(improved_resume)
            st.download_button(
                label="📄 Download Improved Resume",
                data=pdf_buffer,
                file_name="improved_resume.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Error generating PDF: {e}")

elif generate_clicked:
    st.warning("Please upload your resume and enter a job description")
