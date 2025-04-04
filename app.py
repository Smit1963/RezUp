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
    
    report = f"""
    ## ATS Optimization Progress Report
    
    **Original Score**: {original_score}%
    **Optimized Score**: {optimized_score}%
    **Improvement**: {improvement}%
    
    ### Key Improvements:
    - Recovered {len(recovered_keywords)} keywords: {', '.join(recovered_keywords)}
    - Improved formatting for better ATS parsing
    - Enhanced keyword placement and frequency
    
    ### Recommendations:
    {'' if improvement > 5 else 'The optimization needs further work. Consider:'}
    {'' if improvement > 5 else '- More targeted keyword integration'}
    {'' if improvement > 5 else '- Better achievement quantification'}
    {'' if improvement > 5 else '- Improved section organization'}
    """
    return report

# Streamlit UI Setup
st.set_page_config(page_title="RezUp - Resume Optimizer", layout="wide", page_icon="logo.png")

# Custom CSS styling
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
        
        :root {
            --primary: #4CAF50;
            --secondary: #2196F3;
            --accent: #FF5722;
            --skyblue: #87CEEB;
            --darkskyblue: #4682B4;
            --dark: #333333;
            --light: #f8f9fa;
        }
        
        html, body, [class*="css"] {
            font-family: 'Poppins', sans-serif;
            font-size: 18px;
        }
        
        .main-title {
            color: var(--primary);
            font-size: 3.2rem;
            text-align: center;
            margin-bottom: 0.5rem;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        
        .tagline {
            color: var(--dark);
            font-size: 1.5rem;
            text-align: center;
            margin-bottom: 2rem;
            font-weight: 400;
        }
        
        .sub-header {
            color: var(--secondary);
            font-size: 2rem;
            margin: 1.5rem 0 1rem;
            font-weight: 600;
        }
        
        .stButton button {
            background-color: var(--primary);
            color: white;
            border: none;
            padding: 14px 24px;
            text-align: center;
            font-size: 18px;
            margin: 8px 0;
            border-radius: 8px;
            transition: all 0.3s;
            width: 100%;
            font-weight: 600;
        }
        
        .stButton button:hover {
            background-color: var(--secondary);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .generate-btn-container {
            text-align: center;
            margin: 30px 0;
        }
        
        .generate-btn {
            background-color: var(--skyblue) !important;
            color: white !important;
            border: none !important;
            padding: 20px 32px !important;
            text-align: center !important;
            font-size: 36px !important;
            margin: 0 auto !important;
            border-radius: 12px !important;
            transition: all 0.3s !important;
            width: 80% !important;
            font-weight: 700 !important;
            display: inline-block !important;
            cursor: pointer !important;
        }
        
        .generate-btn:hover {
            background-color: var(--darkskyblue) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 12px rgba(0,0,0,0.15) !important;
        }
        
        .stTextArea textarea {
            min-height: 150px;
            font-size: 18px;
            border-radius: 8px;
            padding: 16px;
        }
        
        .stTextArea label, .stFileUploader label {
            font-size: 18px !important;
            font-weight: 500 !important;
        }
        
        .centered {
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            gap: 1.5rem;
            max-width: 800px;
            margin: 0 auto;
        }
        
        .file-uploader {
            width: 100%;
        }
        
        .success-message {
            color: var(--primary);
            font-weight: 600;
            text-align: center;
            margin: 1.2rem 0;
            font-size: 20px;
        }
        
        .action-buttons {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1.2rem;
            margin-top: 2rem;
        }
        
        .response-container {
            font-size: 18px;
            line-height: 1.6;
            padding: 1.5rem;
            border-radius: 10px;
            background-color: #f9f9f9;
            border-left: 4px solid var(--primary);
            margin-top: 1.5rem;
        }
        
        .stAlert {
            font-size: 18px;
            padding: 16px;
        }
        
        .progress-bar {
            height: 20px;
            background-color: #e0e0e0;
            border-radius: 10px;
            margin: 15px 0;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background-color: var(--primary);
            border-radius: 10px;
            transition: width 0.5s;
        }
        
        .score-comparison {
            display: flex;
            justify-content: space-between;
            margin: 20px 0;
        }
        
        .score-box {
            text-align: center;
            padding: 15px;
            border-radius: 8px;
            width: 48%;
        }
        
        .original-score {
            background-color: #ffebee;
            border: 2px solid #ef9a9a;
        }
        
        .optimized-score {
            background-color: #e8f5e9;
            border: 2px solid #a5d6a7;
        }
        
        .score-value {
            font-size: 2.5rem;
            font-weight: 700;
            margin: 10px 0;
        }
        
        @media (max-width: 768px) {
            .action-buttons {
                grid-template-columns: 1fr;
            }
            .generate-btn {
                width: 100% !important;
                font-size: 28px !important;
                padding: 16px 24px !important;
            }
            .score-comparison {
                flex-direction: column;
            }
            .score-box {
                width: 100%;
                margin-bottom: 15px;
            }
        }
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

# Prompts
input_prompt1 = """
As an experienced Technical HR Manager with expertise in data science, AI, and tech fields, review this resume against the job description. 
Provide a professional evaluation of alignment with the role, highlighting:
1. Key strengths matching the job requirements
2. Potential weaknesses or gaps
3. Overall suitability for the position
Include a percentage match score at the top (e.g., "Current match: 65%").
"""

input_prompt2 = """
As a career development coach specializing in tech fields, analyze this resume and job description to:
1. Identify skill gaps between the candidate and job requirements
2. Recommend specific skills to develop
3. Suggest learning resources or pathways
4. Provide actionable improvement steps
"""

input_prompt3 = """
As an ATS optimization expert, evaluate this resume for:
1. Percentage match with the job description (show as % at top)
2. List of present keywords from the job description (with frequency)
3. List of missing keywords from the job description
4. Formatting issues that might affect ATS parsing
5. Final recommendations for improvement
Format clearly with headings for each section and provide specific metrics.
Example format:
Current ATS Match: 65%

Present Keywords:
- Python (3 mentions)
- Machine Learning (2 mentions)

Missing Keywords:
- TensorFlow
- Data Pipelines

Formatting Issues:
- Missing section headers
- Inconsistent bullet points

Recommendations:
1. Add missing keywords naturally in context
2. Standardize formatting
3. Quantify achievements
"""

input_prompt4 = """
As an ATS specialist, identify:
1. The most important missing keywords from the resume
2. Which job requirements aren't addressed
3. Suggested additions to improve ATS ranking
Present in a bullet-point list with priority indicators (High/Medium/Low).
Include a percentage score at the top (e.g., "Current ATS match: 65%").
"""

# Button Handlers
if submit_1:
    if uploaded_file is not None:
        with st.spinner("🔍 Analyzing your resume..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            response = get_gemini_response(input_text, pdf_content, input_prompt1)
            st.markdown('<h2 class="sub-header">🔍 Professional Evaluation</h2>', unsafe_allow_html=True)
            
            # Extract and display score
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
            
            # Extract and display score
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
            
            # Extract and display score
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

if generate_clicked:
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
