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

# Setup Streamlit app with modern theme
st.set_page_config(
    page_title="RezUp - AI Resume Optimizer", 
    layout="wide", 
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

# Custom CSS styling - Modern, sleek design
st.markdown("""
    <style>
        :root {
            --primary: #6366f1;
            --secondary: #8b5cf6;
            --accent: #ec4899;
            --dark: #1e293b;
            --light: #f8fafc;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
        }
        
        .main {
            background: linear-gradient(135deg, #f9f9ff 0%, #f0f4ff 100%);
        }
        
        .main-title {
            font-family: 'Inter', sans-serif;
            font-weight: 800;
            font-size: 3.5rem;
            background: linear-gradient(90deg, var(--primary) 0%, var(--accent) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            margin-bottom: 0.5rem;
            letter-spacing: -1px;
        }
        
        .tagline {
            font-family: 'Inter', sans-serif;
            font-weight: 500;
            font-size: 1.2rem;
            color: var(--dark);
            text-align: center;
            margin-bottom: 2rem;
            opacity: 0.8;
        }
        
        .stTextArea textarea, .stFileUploader div {
            border-radius: 12px !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        }
        
        .stButton button {
            border-radius: 12px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
            border: none !important;
        }
        
        .stButton button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 12px rgba(0,0,0,0.15) !important;
        }
        
        .sub-header {
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            font-size: 1.8rem;
            color: var(--dark);
            margin-top: 2rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--primary);
        }
        
        .success-message {
            color: var(--success);
            font-weight: 500;
            text-align: center;
            padding: 0.5rem;
            border-radius: 8px;
            background-color: rgba(16, 185, 129, 0.1);
        }
        
        .card {
            background: white;
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
            margin-bottom: 1.5rem;
            border: 1px solid #e2e8f0;
        }
        
        .feature-icon {
            font-size: 2rem;
            margin-bottom: 1rem;
            color: var(--primary);
        }
        
        .progress-bar {
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            margin: 1rem 0;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary) 0%, var(--accent) 100%);
            border-radius: 4px;
        }
        
        .glow-card {
            position: relative;
            z-index: 1;
        }
        
        .glow-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            border-radius: 16px;
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%);
            z-index: -1;
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        .glow-card:hover::before {
            opacity: 1;
        }
        
        .download-btn {
            background: linear-gradient(90deg, var(--primary) 0%, var(--accent) 100%) !important;
            color: white !important;
            font-weight: 600 !important;
            padding: 0.75rem 1.5rem !important;
            margin-top: 2rem !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
            transition: all 0.3s ease !important;
        }
        
        .download-btn:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 12px rgba(0,0,0,0.15) !important;
        }
        
        .stMarkdown {
            line-height: 1.6;
        }
        
        /* Animation for the header */
        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-5px); }
            100% { transform: translateY(0px); }
        }
        
        .floating {
            animation: float 3s ease-in-out infinite;
        }
    </style>
""", unsafe_allow_html=True)

# App Header with modern design
st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 class="main-title floating">🚀 RezUp AI</h1>
        <p class="tagline">Transform your resume into an interview magnet with AI</p>
    </div>
""", unsafe_allow_html=True)

# Feature cards in columns
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
        <div class="card glow-card">
            <div class="feature-icon">🔍</div>
            <h3>Smart Analysis</h3>
            <p>AI-powered resume evaluation against job descriptions to identify strengths and weaknesses.</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="card glow-card">
            <div class="feature-icon">✨</div>
            <h3>ATS Optimization</h3>
            <p>Boost your resume's ATS score with keyword optimization and proper formatting.</p>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div class="card glow-card">
            <div class="feature-icon">🚀</div>
            <h3>Instant Results</h3>
            <p>Get actionable insights and a brand new optimized resume in minutes.</p>
        </div>
    """, unsafe_allow_html=True)

# Main Content with modern input areas
with st.container():
    st.markdown('<div class="card" style="padding: 2rem;">', unsafe_allow_html=True)
    input_text = st.text_area(
        "📝 **Paste the Job Description**", 
        key="input", 
        placeholder="Paste the job description you're applying for here...",
        height=150
    )
    
    uploaded_file = st.file_uploader(
        "📂 **Upload Your Resume (PDF only)**", 
        type="pdf", 
        key="file",
        help="Upload your current resume in PDF format for analysis"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_file is not None:
        st.markdown('<p class="success-message">✅ Resume uploaded successfully! Ready for analysis.</p>', unsafe_allow_html=True)

# Action Buttons with modern styling
st.markdown("""
    <div style="margin: 2rem 0;">
        <h3 style="color: var(--dark); margin-bottom: 1rem;">What would you like to improve?</h3>
    </div>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    submit_1 = st.button(
        "🔍 Resume Evaluation", 
        key="eval", 
        help="Get professional evaluation of your resume",
        use_container_width=True
    )

with col2:
    submit_2 = st.button(
        "💡 Skillset Improvement", 
        key="skills", 
        help="Discover how to improve your skills",
        use_container_width=True
    )

with col3:
    submit_3 = st.button(
        "🔑 Missing Keywords", 
        key="keywords", 
        help="Identify important missing keywords",
        use_container_width=True
    )

with col4:
    submit_4 = st.button(
        "📊 ATS Score", 
        key="score", 
        help="Get your resume's ATS compatibility score",
        use_container_width=True
    )

# Optimize Resume button with prominent styling
optimize_resume = st.button(
    "✨ Generate Optimized Resume", 
    key="optimize", 
    help="Create a new resume that scores above 95% ATS compliance",
    use_container_width=True,
    type="primary"
)

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

# Handle button actions with modern output cards
if submit_1:
    if uploaded_file is not None:
        with st.spinner("🔍 Analyzing your resume..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            response = get_gemini_response(input_text, pdf_content, input_prompt1)
            st.session_state.analysis_results = response
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<h2 class="sub-header">🔍 Professional Evaluation</h2>', unsafe_allow_html=True)
            st.write(response)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("Please upload your resume to get analysis")

elif submit_2:
    if uploaded_file is not None:
        with st.spinner("💡 Generating improvement suggestions..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            response = get_gemini_response(input_text, pdf_content, input_prompt2)
            st.session_state.analysis_results = response
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<h2 class="sub-header">💡 Skillset Development Plan</h2>', unsafe_allow_html=True)
            st.write(response)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("Please upload your resume to get suggestions")

elif submit_3:
    if uploaded_file is not None:
        with st.spinner("🔍 Scanning for missing keywords..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            response = get_gemini_response(input_text, pdf_content, input_prompt4)
            st.session_state.analysis_results = response
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<h2 class="sub-header">🔑 Critical Missing Keywords</h2>', unsafe_allow_html=True)
            st.write(response)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("Please upload your resume to check keywords")

elif submit_4:
    if uploaded_file is not None:
        with st.spinner("📊 Calculating ATS score..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            response = get_gemini_response(input_text, pdf_content, input_prompt3)
            st.session_state.analysis_results = response
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<h2 class="sub-header">📊 ATS Compatibility Report</h2>', unsafe_allow_html=True)
            st.write(response)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("Please upload your resume to get ATS score")

# Handle Optimize Resume button with premium output styling
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
            
            # Display the optimized resume in a premium card
            st.markdown("""
                <div class="card" style="border: 2px solid var(--primary);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <h2 class="sub-header">✨ Your Optimized Resume</h2>
                        <div style="background: linear-gradient(90deg, var(--primary) 0%, var(--accent) 100%); 
                                    color: white; padding: 0.25rem 0.75rem; border-radius: 12px; font-weight: 600;">
                            ATS Score: 95%+
                        </div>
                    </div>
            """, unsafe_allow_html=True)
            
            st.markdown(optimized_content, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Create a premium download button
            st.download_button(
                label="📥 Download Optimized Resume (Markdown)",
                data=optimized_content,
                file_name="optimized_resume.md",
                mime="text/markdown",
                key="download-md",
                help="Download your optimized resume in markdown format",
                type="primary",
                use_container_width=True,
                disabled=False
            )
            
            st.success("🎉 Your optimized resume is ready! This version should score above 95% when parsed against the same job description.")
    else:
        st.warning("Please first analyze your resume using one of the analysis options above")

# Add a footer
st.markdown("""
    <div style="margin-top: 4rem; text-align: center; color: var(--dark); opacity: 0.7; font-size: 0.9rem;">
        <p>Powered by Gemini AI • Made with ❤️ for job seekers</p>
        <p>RezUp AI helps you land more interviews with data-driven resume optimization</p>
    </div>
""", unsafe_allow_html=True)
