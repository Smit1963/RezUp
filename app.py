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
st.set_page_config(page_title="RezUp - Resume Optimizer", layout="wide", page_icon="✦︎")

# Custom CSS styling (same as before)
st.markdown("""
    <style>
        /* Your existing CSS styles here */
        .download-btn {
            background-color: var(--accent) !important;
            margin-top: 2rem !important;
        }
        .download-btn:hover {
            background-color: #E64A19 !important;
        }
    </style>
""", unsafe_allow_html=True)

# App Header (same as before)
st.markdown('<h1 class="main-title">✦ RezUp! Till You Make It</h1>', unsafe_allow_html=True)
st.markdown('<p class="tagline">AI that fixes your resume</p>', unsafe_allow_html=True)

# Main Content (same as before)
with st.container():
    st.markdown('<div class="centered">', unsafe_allow_html=True)
    input_text = st.text_area("📝 Enter Job Description", key="input", 
                             placeholder="Paste the job description you're applying for...")
    uploaded_file = st.file_uploader("📂 Upload Your Resume (PDF only)", type="pdf", key="file")
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_file is not None:
        st.markdown('<p class="success-message">✅ Resume uploaded successfully!</p>', unsafe_allow_html=True)

# Action Buttons (updated with new button)
col1, col2 = st.columns(2)
with col1:
    submit_1 = st.button("🔍 Resume Evaluation", key="eval", help="Get professional evaluation of your resume")
    submit_2 = st.button("💡 Skillset Improvement", key="skills", help="Discover how to improve your skills")

with col2:
    submit_3 = st.button("🔑 Missing Keywords", key="keywords", help="Identify important missing keywords")
    submit_4 = st.button("📊 ATS Score", key="score", help="Get your resume's ATS compatibility score")

# New Optimize Resume button
optimize_resume = st.button("✨ Generate Optimized Resume", key="optimize", 
                          help="Create a new resume that scores above 95% ATS compliance")

# Prompts (same as before)
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

# Store analysis results in session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = ""

# Handle button actions (updated to store analysis results)
if submit_1:
    if uploaded_file is not None:
        with st.spinner("🔍 Analyzing your resume..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            response = get_gemini_response(input_text, pdf_content, input_prompt1)
            st.session_state.analysis_results = response
            st.markdown('<h2 class="sub-header">🔍 Professional Evaluation</h2>', unsafe_allow_html=True)
            st.write(response)
    else:
        st.warning("Please upload your resume to get analysis")

elif submit_2:
    if uploaded_file is not None:
        with st.spinner("💡 Generating improvement suggestions..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            response = get_gemini_response(input_text, pdf_content, input_prompt2)
            st.session_state.analysis_results = response
            st.markdown('<h2 class="sub-header">💡 Skillset Development Plan</h2>', unsafe_allow_html=True)
            st.write(response)
    else:
        st.warning("Please upload your resume to get suggestions")

elif submit_3:
    if uploaded_file is not None:
        with st.spinner("🔍 Scanning for missing keywords..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            response = get_gemini_response(input_text, pdf_content, input_prompt4)
            st.session_state.analysis_results = response
            st.markdown('<h2 class="sub-header">🔑 Critical Missing Keywords</h2>', unsafe_allow_html=True)
            st.write(response)
    else:
        st.warning("Please upload your resume to check keywords")

elif submit_4:
    if uploaded_file is not None:
        with st.spinner("📊 Calculating ATS score..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            response = get_gemini_response(input_text, pdf_content, input_prompt3)
            st.session_state.analysis_results = response
            st.markdown('<h2 class="sub-header">📊 ATS Compatibility Report</h2>', unsafe_allow_html=True)
            st.write(response)
    else:
        st.warning("Please upload your resume to get ATS score")

# Handle Optimize Resume button
elif optimize_resume:
    if uploaded_file is not None and input_text and st.session_state.analysis_results:
        with st.spinner("✨ Creating your optimized resume (this may take a minute)..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            
            # Generate the optimized resume content
            optimized_content = generate_optimized_resume(
                input_text, 
                pdf_content, 
                st.session_state.analysis_results
            )
            
            # Display the optimized resume
            st.markdown('<h2 class="sub-header">✨ Your Optimized Resume</h2>', unsafe_allow_html=True)
            st.markdown(optimized_content, unsafe_allow_html=True)
            
            # Create a download button for the resume
            st.download_button(
                label="📥 Download Optimized Resume",
                data=optimized_content,
                file_name="optimized_resume.md",
                mime="text/markdown",
                key="download-md",
                help="Download your optimized resume in markdown format",
                type="primary",
                use_container_width=True,
                on_click=None,
                args=None,
                kwargs=None,
                disabled=False
            )
            
            st.success("Your optimized resume is ready! This version should score above 95% when parsed against the same job description.")
    else:
        st.warning("Please first analyze your resume using one of the analysis options above")
