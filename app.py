import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import io
import base64
import os
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
    1. Incorporates all missing keywords and skills
    2. Maintains the original structure but enhances content
    3. Optimizes for ATS systems
    4. Presents information clearly and professionally
    
    Format the resume with these sections:
    - Header (Name, Contact Info, LinkedIn)
    - Professional Summary
    - Technical Skills (categorized)
    - Work Experience (with quantified achievements)
    - Education
    - Certifications (if any)
    - Projects (if relevant)
    
    Make sure the content is concise, achievement-oriented, and tailored to the job description.
    """
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([input_text, pdf_content[0], prompt])
    return response.text

def create_pdf(resume_text):
    """Create PDF using ReportLab with proper Unicode support"""
    buffer = io.BytesIO()
    styles = getSampleStyleSheet()
    
    # Add custom styles only if they don't exist
    if 'Center' not in styles:
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
    
    if 'SectionHeader' not in styles:
        styles.add(ParagraphStyle(
            name='SectionHeader',
            fontName='Helvetica-Bold',
            fontSize=14,
            spaceAfter=12
        ))
    
    # Use existing BodyText style with modified spacing
    body_style = styles['BodyText']
    body_style.spaceAfter = 6
    
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    
    # Add title
    story.append(Paragraph("Improved Resume", styles['Title']))
    story.append(Spacer(1, 24))
    
    # Process each line
    for line in resume_text.split('\n'):
        if not line.strip():
            story.append(Spacer(1, 12))
            continue
            
        if line.strip().endswith(':'):  # Section header
            story.append(Paragraph(line, styles['SectionHeader']))
        else:
            story.append(Paragraph(line, body_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# Streamlit UI Setup
st.set_page_config(page_title="RezUp - Resume Optimizer", layout="wide", page_icon="logo.png")

# Custom CSS styling
st.markdown("""
    <style>
        /* [Previous CSS styles remain exactly the same] */
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

# Prompts (same as before)
input_prompt1 = """..."""
input_prompt2 = """..."""
input_prompt3 = """..."""
input_prompt4 = """..."""

# Button Handlers
if submit_1:
    if uploaded_file is not None:
        with st.spinner("🔍 Analyzing your resume..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            response = get_gemini_response(input_text, pdf_content, input_prompt1)
            st.markdown('<h2 class="sub-header">🔍 Professional Evaluation</h2>', unsafe_allow_html=True)
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
            st.markdown(f'<div class="response-container">{response}</div>', unsafe_allow_html=True)
    else:
        st.warning("Please upload your resume to check keywords")

elif submit_4:
    if uploaded_file is not None:
        with st.spinner("📊 Calculating ATS score..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            response = get_gemini_response(input_text, pdf_content, input_prompt3)
            st.markdown('<h2 class="sub-header">📊 ATS Compatibility Report</h2>', unsafe_allow_html=True)
            st.markdown(f'<div class="response-container">{response}</div>', unsafe_allow_html=True)
    else:
        st.warning("Please upload your resume to get ATS score")

if generate_clicked:
    if uploaded_file is not None:
        with st.spinner("✨ Creating your optimized resume..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            improved_resume = generate_improved_resume(input_text, pdf_content)
            
            st.markdown('<h2 class="sub-header">✨ Optimized Resume</h2>', unsafe_allow_html=True)
            st.markdown(f'<div class="response-container">{improved_resume}</div>', unsafe_allow_html=True)
            
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
                st.info("Please try again or contact support if the problem persists.")
    else:
        st.warning("Please upload your resume to generate an improved version")
