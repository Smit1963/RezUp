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

# [Rest of your original Streamlit UI code remains exactly the same...]
# [Include all your original Streamlit setup, styling, and button handlers]

# Only change needed in the button handler is to combine content for PDF:
if generate_clicked:
    if uploaded_file is not None and input_text:
        with st.spinner("✨ Creating your optimized resume..."):
            # [Keep all your original evaluation code...]
            
            # Generate combined content for PDF
            pdf_content = f"{improved_resume}\n\n{progress_report}"
            pdf_buffer = create_pdf(pdf_content)
            
            # [Keep all your original display code...]
            
            # Download button
            st.download_button(
                label="📄 Download Improved Resume (PDF)",
                data=pdf_buffer,
                file_name="improved_resume.pdf",
                mime="application/pdf"
            )
