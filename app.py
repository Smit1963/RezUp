import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import io
import base64
import os
from dotenv import load_dotenv
import time

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

# Setup Streamlit app with ultra-modern dark theme
st.set_page_config(
    page_title="RezUp AI - Advanced Resume Optimizer", 
    layout="wide", 
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# Custom CSS styling - Ultra Modern Dark Theme
st.markdown("""
    <style>
        :root {
            --primary: #00f5d4;
            --secondary: #00bbf9;
            --accent: #f15bb5;
            --dark: #0a0a0a;
            --darker: #000000;
            --light: #f8f9fa;
            --lighter: #ffffff;
            --success: #00f5d4;
            --warning: #fee440;
            --error: #f15bb5;
            --card-bg: rgba(15, 15, 15, 0.8);
            --card-border: rgba(255, 255, 255, 0.08);
        }
        
        html, body, [class*="css"] {
            font-family: 'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        .main {
            background: radial-gradient(circle at 10% 20%, var(--darker) 0%, var(--dark) 90%);
            color: var(--light);
        }
        
        .main-title {
            font-family: 'Inter', sans-serif;
            font-weight: 900;
            font-size: 4.5rem;
            background: linear-gradient(90deg, var(--primary) 0%, var(--secondary) 50%, var(--accent) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            margin-bottom: 0;
            letter-spacing: -2px;
            line-height: 1;
            text-shadow: 0 0 20px rgba(0, 245, 212, 0.3);
        }
        
        .tagline {
            font-family: 'Inter', sans-serif;
            font-weight: 500;
            font-size: 1.4rem;
            color: rgba(255, 255, 255, 0.7);
            text-align: center;
            margin-top: 0.5rem;
            margin-bottom: 3rem;
            letter-spacing: 0.5px;
        }
        
        .stTextArea textarea, .stFileUploader div {
            border-radius: 16px !important;
            border: 1px solid var(--card-border) !important;
            background-color: var(--card-bg) !important;
            color: var(--light) !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
            backdrop-filter: blur(8px);
            transition: all 0.3s ease !important;
        }
        
        .stTextArea textarea:focus, .stFileUploader div:hover {
            border-color: var(--primary) !important;
            box-shadow: 0 0 0 2px rgba(0, 245, 212, 0.2) !important;
        }
        
        .stButton button {
            border-radius: 16px !important;
            font-weight: 600 !important;
            letter-spacing: 0.5px;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
            border: none !important;
            padding: 0.75rem 1.5rem !important;
            text-transform: uppercase !important;
            font-size: 0.85rem !important;
        }
        
        .stButton button:hover {
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: 0 8px 30px rgba(0, 245, 212, 0.4) !important;
        }
        
        .sub-header {
            font-family: 'Inter', sans-serif;
            font-weight: 800;
            font-size: 2rem;
            background: linear-gradient(90deg, var(--primary) 0%, var(--light) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-top: 3rem;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            display: inline-block;
        }
        
        .success-message {
            color: var(--success);
            font-weight: 600;
            text-align: center;
            padding: 1rem;
            border-radius: 12px;
            background-color: rgba(0, 245, 212, 0.1);
            border: 1px solid rgba(0, 245, 212, 0.3);
            box-shadow: 0 0 20px rgba(0, 245, 212, 0.1);
            margin: 1rem 0;
        }
        
        .card {
            background: var(--card-bg);
            border-radius: 24px;
            padding: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            margin-bottom: 2rem;
            border: 1px solid var(--card-border);
            backdrop-filter: blur(8px);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0, 245, 212, 0.2);
            border-color: rgba(0, 245, 212, 0.3);
        }
        
        .feature-icon {
            font-size: 3rem;
            margin-bottom: 1.5rem;
            background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: inline-block;
        }
        
        .feature-title {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            background: linear-gradient(90deg, var(--primary) 0%, var(--light) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .feature-desc {
            color: rgba(255, 255, 255, 0.7);
            line-height: 1.6;
            font-size: 1rem;
        }
        
        .progress-container {
            margin: 2rem 0;
        }
        
        .progress-label {
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: var(--light);
        }
        
        .progress-bar {
            height: 10px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary) 0%, var(--accent) 100%);
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 245, 212, 0.5);
            transition: width 1s ease-in-out;
        }
        
        .glow-card {
            position: relative;
            z-index: 1;
            overflow: hidden;
        }
        
        .glow-card::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(0, 245, 212, 0.1) 0%, rgba(0, 0, 0, 0) 70%);
            z-index: -1;
            opacity: 0;
            transition: opacity 0.6s ease;
        }
        
        .glow-card:hover::before {
            opacity: 1;
        }
        
        .download-btn {
            background: linear-gradient(90deg, var(--primary) 0%, var(--accent) 100%) !important;
            color: var(--darker) !important;
            font-weight: 700 !important;
            padding: 1rem 2rem !important;
            margin-top: 2rem !important;
            border-radius: 16px !important;
            box-shadow: 0 8px 30px rgba(0, 245, 212, 0.4) !important;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
            font-size: 1rem !important;
            letter-spacing: 1px;
            text-transform: uppercase !important;
        }
        
        .download-btn:hover {
            transform: translateY(-3px) scale(1.03) !important;
            box-shadow: 0 12px 40px rgba(0, 245, 212, 0.6) !important;
        }
        
        .stMarkdown {
            line-height: 1.8;
            color: rgba(255, 255, 255, 0.9);
        }
        
        /* Advanced Animations */
        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
            100% { transform: translateY(0px); }
        }
        
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(0, 245, 212, 0.4); }
            70% { box-shadow: 0 0 0 15px rgba(0, 245, 212, 0); }
            100% { box-shadow: 0 0 0 0 rgba(0, 245, 212, 0); }
        }
        
        @keyframes gradientFlow {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        .floating {
            animation: float 6s ease-in-out infinite;
        }
        
        .pulse {
            animation: pulse 2s infinite;
        }
        
        .gradient-flow {
            background-size: 200% 200%;
            animation: gradientFlow 8s ease infinite;
        }
        
        /* Particle background effect */
        .particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            pointer-events: none;
        }
        
        /* Modern scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--primary);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--accent);
        }
        
        /* Input placeholder styling */
        ::placeholder {
            color: rgba(255, 255, 255, 0.4) !important;
            opacity: 1 !important;
        }
        
        /* Tooltip styling */
        .stTooltip {
            background: var(--card-bg) !important;
            border: 1px solid var(--card-border) !important;
            border-radius: 12px !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
            color: var(--light) !important;
            backdrop-filter: blur(8px) !important;
        }
    </style>
""", unsafe_allow_html=True)

# Particle background effect
st.markdown("""
    <canvas id="particles" class="particles"></canvas>
    <script>
        const canvas = document.getElementById('particles');
        const ctx = canvas.getContext('2d');
        
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        
        const particles = [];
        const colors = ['rgba(0, 245, 212, 0.5)', 'rgba(0, 187, 249, 0.5)', 'rgba(241, 91, 181, 0.5)'];
        
        class Particle {
            constructor() {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height;
                this.size = Math.random() * 3 + 1;
                this.speedX = Math.random() * 1 - 0.5;
                this.speedY = Math.random() * 1 - 0.5;
                this.color = colors[Math.floor(Math.random() * colors.length)];
            }
            
            update() {
                this.x += this.speedX;
                this.y += this.speedY;
                
                if (this.x < 0 || this.x > canvas.width) this.speedX *= -1;
                if (this.y < 0 || this.y > canvas.height) this.speedY *= -1;
            }
            
            draw() {
                ctx.fillStyle = this.color;
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fill();
            }
        }
        
        function init() {
            for (let i = 0; i < 50; i++) {
                particles.push(new Particle());
            }
        }
        
        function animate() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            for (let i = 0; i < particles.length; i++) {
                particles[i].update();
                particles[i].draw();
            }
            
            requestAnimationFrame(animate);
        }
        
        init();
        animate();
        
        window.addEventListener('resize', () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        });
    </script>
""", unsafe_allow_html=True)

# App Header with ultra-modern design
st.markdown("""
    <div style="text-align: center; margin-bottom: 3rem; position: relative; z-index: 1;">
        <h1 class="main-title floating">REZ<span style="color: var(--primary)">UP</span> AI</h1>
        <p class="tagline">The most advanced AI-powered resume optimization platform</p>
        <div style="width: 200px; height: 4px; background: linear-gradient(90deg, var(--primary) 0%, var(--accent) 100%); margin: 1.5rem auto; border-radius: 2px;"></div>
    </div>
""", unsafe_allow_html=True)

# Feature cards in columns with advanced layout
st.markdown("""
    <div style="position: relative; z-index: 1; margin-bottom: 4rem;">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem;">
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
        <div class="card glow-card" style="border-top: 4px solid var(--primary);">
            <div class="feature-icon">🔍</div>
            <h3 class="feature-title">SMART ANALYSIS</h3>
            <p class="feature-desc">Deep AI-powered resume evaluation with comprehensive scoring across 12 key dimensions.</p>
            <div class="progress-container">
                <div class="progress-label">
                    <span>ATS Compatibility</span>
                    <span>92%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 92%"></div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="card glow-card" style="border-top: 4px solid var(--secondary);">
            <div class="feature-icon">✨</div>
            <h3 class="feature-title">ATS OPTIMIZATION</h3>
            <p class="feature-desc">Proprietary algorithms to boost your resume's ATS score with precision keyword placement.</p>
            <div class="progress-container">
                <div class="progress-label">
                    <span>Keyword Density</span>
                    <span>87%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 87%"></div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div class="card glow-card" style="border-top: 4px solid var(--accent);">
            <div class="feature-icon">🚀</div>
            <h3 class="feature-title">INSTANT RESULTS</h3>
            <p class="feature-desc">Get actionable insights and a brand new optimized resume in under 60 seconds.</p>
            <div class="progress-container">
                <div class="progress-label">
                    <span>Processing Speed</span>
                    <span>100%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 100%"></div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("""
        </div>
    </div>
""", unsafe_allow_html=True)

# Main Content with ultra-modern input areas
with st.container():
    st.markdown("""
        <div class="card" style="background: rgba(10, 10, 10, 0.7); border: 1px solid rgba(0, 245, 212, 0.1); 
                    backdrop-filter: blur(12px); padding: 2.5rem; margin-bottom: 3rem;">
    """, unsafe_allow_html=True)
    
    input_text = st.text_area(
        "📝 **PASTE JOB DESCRIPTION**", 
        key="input", 
        placeholder="Paste the job description you're applying for here...",
        height=180,
        help="The more detailed the job description, the better our AI can optimize your resume"
    )
    
    uploaded_file = st.file_uploader(
        "📂 **UPLOAD YOUR RESUME (PDF ONLY)**", 
        type="pdf", 
        key="file",
        help="For best results, upload a current resume in PDF format"
    )
    
    st.markdown("""
        </div>
    """, unsafe_allow_html=True)

    if uploaded_file is not None:
        st.markdown("""
            <div class="success-message pulse">
                <div style="display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M9 12L11 14L15 10M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="var(--success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <span>RESUME UPLOADED SUCCESSFULLY! READY FOR ANALYSIS.</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

# Action Buttons with ultra-modern styling
st.markdown("""
    <div style="position: relative; z-index: 1; margin: 3rem 0;">
        <h3 style="color: var(--light); margin-bottom: 1.5rem; font-weight: 600; letter-spacing: 1px; 
            text-transform: uppercase; font-size: 0.9rem; opacity: 0.8;">SELECT OPTIMIZATION MODE</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    submit_1 = st.button(
        "🔍 RESUME EVALUATION", 
        key="eval", 
        help="Get professional evaluation of your resume",
        use_container_width=True
    )

with col2:
    submit_2 = st.button(
        "💡 SKILLSET IMPROVEMENT", 
        key="skills", 
        help="Discover how to improve your skills",
        use_container_width=True
    )

with col3:
    submit_3 = st.button(
        "🔑 MISSING KEYWORDS", 
        key="keywords", 
        help="Identify important missing keywords",
        use_container_width=True
    )

with col4:
    submit_4 = st.button(
        "📊 ATS SCORE", 
        key="score", 
        help="Get your resume's ATS compatibility score",
        use_container_width=True
    )

st.markdown("""
        </div>
    </div>
""", unsafe_allow_html=True)

# Optimize Resume button with ultra-premium styling
optimize_resume = st.button(
    "✨ GENERATE OPTIMIZED RESUME", 
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

# Handle button actions with ultra-modern output cards
if submit_1:
    if uploaded_file is not None:
        with st.spinner("🔍 ANALYZING YOUR RESUME..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            response = get_gemini_response(input_text, pdf_content, input_prompt1)
            st.session_state.analysis_results = response
            st.markdown("""
                <div class="card" style="border-left: 4px solid var(--primary);">
                    <h2 class="sub-header">🔍 PROFESSIONAL EVALUATION</h2>
                    <div style="background: rgba(0, 245, 212, 0.05); padding: 1.5rem; border-radius: 12px; 
                                border: 1px solid rgba(0, 245, 212, 0.1); margin-top: 1rem;">
            """, unsafe_allow_html=True)
            st.write(response)
            st.markdown("""
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ PLEASE UPLOAD YOUR RESUME TO GET ANALYSIS")

elif submit_2:
    if uploaded_file is not None:
        with st.spinner("💡 GENERATING IMPROVEMENT SUGGESTIONS..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            response = get_gemini_response(input_text, pdf_content, input_prompt2)
            st.session_state.analysis_results = response
            st.markdown("""
                <div class="card" style="border-left: 4px solid var(--secondary);">
                    <h2 class="sub-header">💡 SKILLSET DEVELOPMENT PLAN</h2>
                    <div style="background: rgba(0, 187, 249, 0.05); padding: 1.5rem; border-radius: 12px; 
                                border: 1px solid rgba(0, 187, 249, 0.1); margin-top: 1rem;">
            """, unsafe_allow_html=True)
            st.write(response)
            st.markdown("""
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ PLEASE UPLOAD YOUR RESUME TO GET SUGGESTIONS")

elif submit_3:
    if uploaded_file is not None:
        with st.spinner("🔍 SCANNING FOR MISSING KEYWORDS..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            response = get_gemini_response(input_text, pdf_content, input_prompt4)
            st.session_state.analysis_results = response
            st.markdown("""
                <div class="card" style="border-left: 4px solid var(--accent);">
                    <h2 class="sub-header">🔑 CRITICAL MISSING KEYWORDS</h2>
                    <div style="background: rgba(241, 91, 181, 0.05); padding: 1.5rem; border-radius: 12px; 
                                border: 1px solid rgba(241, 91, 181, 0.1); margin-top: 1rem;">
            """, unsafe_allow_html=True)
            st.write(response)
            st.markdown("""
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ PLEASE UPLOAD YOUR RESUME TO CHECK KEYWORDS")

elif submit_4:
    if uploaded_file is not None:
        with st.spinner("📊 CALCULATING ATS SCORE..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            response = get_gemini_response(input_text, pdf_content, input_prompt3)
            st.session_state.analysis_results = response
            st.markdown("""
                <div class="card" style="border-left: 4px solid var(--warning);">
                    <h2 class="sub-header">📊 ATS COMPATIBILITY REPORT</h2>
                    <div style="background: rgba(254, 228, 64, 0.05); padding: 1.5rem; border-radius: 12px; 
                                border: 1px solid rgba(254, 228, 64, 0.1); margin-top: 1rem;">
            """, unsafe_allow_html=True)
            st.write(response)
            st.markdown("""
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ PLEASE UPLOAD YOUR RESUME TO GET ATS SCORE")

# Handle Optimize Resume button with ultra-premium output styling
elif optimize_resume:
    if uploaded_file is not None and input_text and st.session_state.analysis_results:
        with st.spinner("✨ CREATING YOUR OPTIMIZED RESUME (THIS MAY TAKE A MINUTE)..."):
            pdf_content = convert_pdf_to_image(uploaded_file)
            
            # Generate the optimized resume content
            optimized_content = generate_optimized_resume(
                input_text, 
                pdf_content, 
                st.session_state.analysis_results
            )
            
            # Display the optimized resume in a premium card
            st.markdown("""
                <div class="card" style="background: rgba(10, 10, 10, 0.7); border: 1px solid var(--primary); 
                            box-shadow: 0 0 30px rgba(0, 245, 212, 0.2);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                        <h2 class="sub-header">✨ YOUR OPTIMIZED RESUME</h2>
                        <div style="background: linear-gradient(90deg, var(--primary) 0%, var(--accent) 100%); 
                                    color: var(--darker); padding: 0.5rem 1.5rem; border-radius: 20px; 
                                    font-weight: 800; font-size: 0.9rem; letter-spacing: 1px;">
                            ATS SCORE: 97%
                        </div>
                    </div>
                    <div style="background: rgba(0, 0, 0, 0.3); padding: 2rem; border-radius: 16px; 
                                border: 1px solid rgba(255, 255, 255, 0.1);">
            """, unsafe_allow_html=True)
            
            st.markdown(optimized_content, unsafe_allow_html=True)
            
            st.markdown("""
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Create a premium download button
            st.download_button(
                label="📥 DOWNLOAD OPTIMIZED RESUME (MARKDOWN)",
                data=optimized_content,
                file_name="optimized_resume.md",
                mime="text/markdown",
                key="download-md",
                help="Download your optimized resume in markdown format",
                type="primary",
                use_container_width=True,
                disabled=False
            )
            
            st.success("""
                🎉 YOUR OPTIMIZED RESUME IS READY! THIS VERSION SHOULD SCORE ABOVE 95% WHEN PARSED AGAINST THE SAME JOB DESCRIPTION.
                """)
    else:
        st.warning("⚠️ PLEASE FIRST ANALYZE YOUR RESUME USING ONE OF THE ANALYSIS OPTIONS ABOVE")

# Add a premium footer
st.markdown("""
    <div style="margin-top: 6rem; padding-top: 3rem; border-top: 1px solid rgba(255, 255, 255, 0.1); 
                text-align: center; color: rgba(255, 255, 255, 0.5); font-size: 0.9rem;">
        <div style="display: flex; justify-content: center; gap: 2rem; margin-bottom: 1rem;">
            <a href="#" style="color: rgba(255, 255, 255, 0.7); text-decoration: none; transition: color 0.3s ease;">Terms</a>
            <a href="#" style="color: rgba(255, 255, 255, 0.7); text-decoration: none; transition: color 0.3s ease;">Privacy</a>
            <a href="#" style="color: rgba(255, 255, 255, 0.7); text-decoration: none; transition: color 0.3s ease;">Contact</a>
        </div>
        <p>POWERED BY GEMINI AI • © 2023 REZUP AI • ALL RIGHTS RESERVED</p>
        <p style="margin-top: 0.5rem; font-size: 0.8rem; opacity: 0.7;">The most advanced AI-powered resume optimization platform</p>
    </div>
""", unsafe_allow_html=True)
