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
    
    # Create styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='SectionHeader', 
                            fontName='Helvetica-Bold',
                            fontSize=14,
                            spaceAfter=12))
    styles.add(ParagraphStyle(name='BodyText', 
                            fontName='Helvetica',
                            fontSize=12,
                            leading=14,
                            spaceAfter=6))
    
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
            story.append(Paragraph(line, styles['BodyText']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# [Previous Streamlit UI code remains exactly the same until the generate_clicked section]

elif generate_clicked:
    if uploaded_file is not None:
        with st.spinner("✨ Creating your optimized resume..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            improved_resume = generate_improved_resume(input_text, pdf_content)
            
            st.markdown('<h2 class="sub-header">✨ Optimized Resume</h2>', unsafe_allow_html=True)
            st.markdown(f'<div class="response-container">{improved_resume}</div>', unsafe_allow_html=True)
            
            # Create PDF using ReportLab
            try:
                pdf_buffer = create_pdf(improved_resume)
                st.download_button(
                    label="📄 Download Improved Resume (PDF)",
                    data=pdf_buffer,
                    file_name="improved_resume.pdf",
                    mime="application/pdf",
                    key="download-resume",
                    help="Download your optimized resume as a PDF file",
                    type="primary",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")
                st.info("Please try again or contact support if the problem persists.")
    else:
        st.warning("Please upload your resume to generate an improved version")
