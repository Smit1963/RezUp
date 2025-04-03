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
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to get Gemini response
def get_gemini_response(input_text, pdf_content, prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([input_text, pdf_content[0], prompt])
    return response.text

# Function to generate optimized resume
def generate_optimized_resume(input_text, pdf_content, analysis_results):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    Based on the following job description and resume analysis, create a brand new optimized resume that:
    1. Incorporates all the missing keywords identified
    2. Addresses all skill gaps mentioned
    3. Follows ATS best practices
    4. Will score above 95% when parsed against the same job description
    
    Job Description:
    {input_text}
    
    Original Resume Content:
    {pdf_content[0]}
    
    Analysis Results:
    {analysis_results}
    
    Create a professional resume in markdown format that includes:
    - Clean, modern formatting
    - All necessary sections (Summary, Experience, Skills, Education, etc.)
    - Proper keyword placement
    - Quantifiable achievements
    - Action verbs
    
    Return ONLY the resume content in markdown format, ready to be converted to PDF.
    """
    response = model.generate_content(prompt)
    return response.text

# Function to convert PDF to image
def convert_pdf_to_image(uploaded_file):
    pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    page = pdf_document.load_page(0)  # Load the first page
    pix = page.get_pixmap()
    
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()
    
    return [{"mime_type": "image/jpeg", "data": base64.b64encode(img_byte_arr).decode()}]

# Setup Streamlit app
st.set_page_config(page_title="RezUp - Resume Optimizer", layout="wide", page_icon="✦︎")

# Custom CSS styling
st.markdown("""
    <style>
        .download-btn {
            background-color: var(--accent) !important;
            margin-top: 2rem !important;
        }
        .download-btn:hover {
            background-color: #E64A19 !important;
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

# Action Buttons
col1, col2 = st.columns(2)
with col1:
    submit_1 = st.button("🔍 Resume Evaluation", key="eval")
    submit_2 = st.button("💡 Skillset Improvement", key="skills")

with col2:
    submit_3 = st.button("🔑 Missing Keywords", key="keywords")
    submit_4 = st.button("📊 ATS Score", key="score")

# New Optimize Resume button
optimize_resume = st.button("✨ Generate Optimized Resume", key="optimize")

# Store analysis results in session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = ""

# Handle button actions
def handle_analysis(button_key, prompt, title):
    if uploaded_file is not None:
        with st.spinner(f"🔍 {title}..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            response = get_gemini_response(input_text, pdf_content, prompt)
            st.session_state.analysis_results = response
            st.markdown(f'<h2 class="sub-header">🔍 {title}</h2>', unsafe_allow_html=True)
            st.write(response)
    else:
        st.warning("Please upload your resume to get analysis")

if submit_1:
    handle_analysis("eval", input_prompt1, "Professional Evaluation")
elif submit_2:
    handle_analysis("skills", input_prompt2, "Skillset Development Plan")
elif submit_3:
    handle_analysis("keywords", input_prompt4, "Critical Missing Keywords")
elif submit_4:
    handle_analysis("score", input_prompt3, "ATS Compatibility Report")

# Handle Optimize Resume button
if optimize_resume:
    if uploaded_file is not None and input_text and st.session_state.analysis_results:
        with st.spinner("✨ Creating your optimized resume (this may take a minute)..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            optimized_content = generate_optimized_resume(
                input_text, 
                pdf_content, 
                st.session_state.analysis_results
            )
            st.markdown('<h2 class="sub-header">✨ Your Optimized Resume</h2>', unsafe_allow_html=True)
            st.markdown(optimized_content, unsafe_allow_html=True)
            st.download_button(
                label="📥 Download Optimized Resume",
                data=optimized_content,
                file_name="optimized_resume.md",
                mime="text/markdown",
                key="download-md",
                help="Download your optimized resume in markdown format",
                type="primary",
                use_container_width=True
            )
            st.success("Your optimized resume is ready! This version should score above 95% when parsed against the same job description.")
    else:
        st.warning("Please first analyze your resume using one of the analysis options above")
