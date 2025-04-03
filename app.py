import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import io
import base64
import os
from dotenv import load_dotenv

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

# Setup Streamlit app
st.set_page_config(page_title="RezUp - Resume Optimizer", layout="wide", page_icon="✦")

# Custom CSS styling with larger fonts
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
        
        :root {
            --primary: #4CAF50;
            --secondary: #2196F3;
            --accent: #FF5722;
            --dark: #333333;
            --light: #f8f9fa;
        }
        
        html, body, [class*="css"] {
            font-family: 'Poppins', sans-serif;
            font-size: 18px; /* Increased base font size */
        }
        
        .main-title {
            color: var(--primary);
            font-size: 3.2rem; /* Increased from 2.8rem */
            text-align: center;
            margin-bottom: 0.5rem;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        
        .tagline {
            color: var(--dark);
            font-size: 1.5rem; /* Increased from 1.3rem */
            text-align: center;
            margin-bottom: 2rem;
            font-weight: 400;
        }
        
        .sub-header {
            color: var(--secondary);
            font-size: 2rem; /* Increased from 1.8rem */
            margin: 1.5rem 0 1rem;
            font-weight: 600;
        }
        
        .stButton button {
            background-color: var(--primary);
            color: white;
            border: none;
            padding: 14px 24px; /* Increased padding */
            text-align: center;
            font-size: 18px; /* Increased from 16px */
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
        
        .stTextArea textarea {
            min-height: 150px;
            font-size: 18px; /* Increased from 16px */
            border-radius: 8px;
            padding: 16px; /* Increased padding */
        }
        
        /* Increase label font sizes */
        .stTextArea label, .stFileUploader label {
            font-size: 18px !important;
            font-weight: 500 !important;
        }
        
        .centered {
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            gap: 1.5rem; /* Increased from 1rem */
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
            margin: 1.2rem 0; /* Increased */
            font-size: 20px; /* Added explicit font size */
        }
        
        .action-buttons {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1.2rem; /* Increased from 1rem */
            margin-top: 2rem; /* Increased from 1.5rem */
        }
        
        /* Response text container */
        .response-container {
            font-size: 18px;
            line-height: 1.6;
            padding: 1.5rem;
            border-radius: 10px;
            background-color: #f9f9f9;
            border-left: 4px solid var(--primary);
            margin-top: 1.5rem;
        }
        
        /* Make warning messages more readable */
        .stAlert {
            font-size: 18px;
            padding: 16px;
        }
        
        @media (max-width: 768px) {
            .action-buttons {
                grid-template-columns: 1fr;
            }
        }
    </style>
""", unsafe_allow_html=True)

# App Header
st.markdown('<h1 class="main-title">✦ RezUp! Till You Make It</h1>', unsafe_allow_html=True)
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

# Action Buttons in one line
st.markdown('<div class="action-buttons">', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)
with col1:
    submit_1 = st.button("🔍 Resume Evaluation", key="eval", help="Get professional evaluation of your resume")
with col2:
    submit_2 = st.button("💡 Skillset Improvement", key="skills", help="Discover how to improve your skills")
with col3:
    submit_3 = st.button("🔑 Missing Keywords", key="keywords", help="Identify important missing keywords")
with col4:
    submit_4 = st.button("📊 ATS Score", key="score", help="Get your resume's ATS compatibility score")
st.markdown('</div>', unsafe_allow_html=True)

# Prompts
input_prompt1 = """
As an experienced Technical HR Manager with expertise in data science, AI, and tech fields, review this resume against the job description. 
Provide a professional evaluation of alignment with the role, highlighting:
1. Key strengths matching the job requirements
2. Potential weaknesses or gaps
3. Overall suitability for the position
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
2. List of missing keywords from the resume
3. Critical hard skills that are absent
4. Final recommendations for improvement
Format clearly with headings for each section.
"""

input_prompt4 = """
As an ATS specialist, identify:
1. The most important missing keywords from the resume
2. Which job requirements aren't addressed
3. Suggested additions to improve ATS ranking
Present in a bullet-point list with priority indicators (High/Medium/Low).
"""

# Handle button actions
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
