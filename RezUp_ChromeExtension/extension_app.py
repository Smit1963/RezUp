import google.generativeai as genai
from PIL import Image
import fitz
import io
import base64
import os
import re
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from flask import Flask, request, jsonify
from flask_cors import CORS  # For handling cross-origin requests

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

def get_gemini_response(input_text, pdf_content, prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    if pdf_content:
        response = model.generate_content([input_text, pdf_content[0], prompt])
    else:
        response = model.generate_content([input_text, prompt])
    return response.text

def convert_pdf_to_text(uploaded_file):
    text = ""
    try:
        pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
    except Exception as e:
        print(f"Error converting PDF to text: {e}")
    return [{"mime_type": "text/plain", "data": base64.b64encode(text.encode('utf-8')).decode('utf-8')}]

def generate_improved_resume(input_text, pdf_content):
    prompt = """Based on the job description and current resume, generate an improved resume that:
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
    Include specific keywords from the job description naturally in context."""
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([input_text, pdf_content[0], prompt])
    return response.text

def create_pdf(resume_text):
    buffer = io.BytesIO()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='RezUpHeader', fontName='Helvetica-Bold', fontSize=16, spaceAfter=12))
    styles.add(ParagraphStyle(name='RezUpSubheader', fontName='Helvetica-Bold', fontSize=14, spaceAfter=8))
    styles.add(ParagraphStyle(name='RezUpBody', fontSize=12, leading=14, spaceAfter=6))
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
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
    return buffer.getvalue()

def extract_score_from_evaluation(evaluation_text):
    match = re.search(r'(\d{1,3})%', evaluation_text)
    return int(match.group(1)) if match else 0

def extract_missing_keywords(evaluation_text):
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
    improvement = optimized_score - original_score
    recovered_keywords = set(original_missing) - set(optimized_missing)
    return {
        "original_score": original_score,
        "optimized_score": optimized_score,
        "improvement": improvement,
        "recovered_keywords": list(recovered_keywords),
        "remaining_missing": list(set(optimized_missing))
    }

input_prompt1 = """As an experienced Technical HR Manager with expertise in data science, AI, and tech fields, review this resume against the job description.
Provide a professional evaluation of alignment with the role, highlighting:
1. Key strengths matching the job requirements
2. Potential weaknesses or gaps
3. Overall suitability for the position
Include a percentage match score at the top (e.g., "Current match: 65%")."""

input_prompt2 = """As a career development coach specializing in tech fields, analyze this resume and job description to:
1. Identify skill gaps between the candidate and job requirements
2. Recommend specific skills to develop
3. Suggest learning resources or pathways
4. Provide actionable improvement steps"""

input_prompt3 = """As an ATS optimization expert, evaluate this resume for:
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
3. Quantify achievements"""

input_prompt4 = """As an ATS specialist, identify:
1. The most important missing keywords from the resume
2. Which job requirements aren't addressed
3. Suggested additions to improve ATS ranking
Present in a bullet-point list with priority indicators (High/Medium/Low).
Include a percentage score at the top (e.g., "Current ATS match: 65%")."""

@app.route('/evaluate', methods=['POST'])
def evaluate_resume():
    job_description = request.form.get('job_description')
    resume_file = request.files.get('resume')
    if not job_description or not resume_file:
        return jsonify({"error": "Job description and resume are required"}), 400
    pdf_content = convert_pdf_to_text(resume_file)
    response = get_gemini_response(job_description, pdf_content, input_prompt1)
    score = extract_score_from_evaluation(response)
    return jsonify({"evaluation": response, "score": score})

@app.route('/skills', methods=['POST'])
def suggest_skills():
    job_description = request.form.get('job_description')
    resume_file = request.files.get('resume')
    if not job_description or not resume_file:
        return jsonify({"error": "Job description and resume are required"}), 400
    pdf_content = convert_pdf_to_text(resume_file)
    response = get_gemini_response(job_description, pdf_content, input_prompt2)
    return jsonify({"suggestions": response})

@app.route('/keywords', methods=['POST'])
def find_missing_keywords():
    job_description = request.form.get('job_description')
    resume_file = request.files.get('resume')
    if not job_description or not resume_file:
        return jsonify({"error": "Job description and resume are required"}), 400
    pdf_content = convert_pdf_to_text(resume_file)
    response = get_gemini_response(job_description, pdf_content, input_prompt4)
    score = extract_score_from_evaluation(response)
    return jsonify({"keywords": response, "score": score})

@app.route('/score', methods=['POST'])
def get_ats_score():
    job_description = request.form.get('job_description')
    resume_file = request.files.get('resume')
    if not job_description or not resume_file:
        return jsonify({"error": "Job description and resume are required"}), 400
    pdf_content = convert_pdf_to_text(resume_file)
    response = get_gemini_response(job_description, pdf_content, input_prompt3)
    score = extract_score_from_evaluation(response)
    return jsonify({"ats_report": response, "score": score})

@app.route('/generate', methods=['POST'])
def generate_resume():
    job_description = request.form.get('job_description')
    resume_file = request.files.get('resume')
    if not job_description or not resume_file:
        return jsonify({"error": "Job description and resume are required"}), 400
    pdf_content = convert_pdf_to_text(resume_file)
    original_evaluation = get_gemini_response(job_description, pdf_content, input_prompt3)
    original_score = extract_score_from_evaluation(original_evaluation)
    original_missing = extract_missing_keywords(original_evaluation)
    improved_resume = generate_improved_resume(job_description, pdf_content)
    improved_content = [{"mime_type": "text/plain", "data": base64.b64encode(improved_resume.encode()).decode('utf-8')}]
    improved_evaluation = get_gemini_response(job_description, improved_content, input_prompt3)
    improved_score = extract_score_from_evaluation(improved_evaluation)
    improved_missing = extract_missing_keywords(improved_evaluation)
    progress_data = evaluate_resume_progress(original_score, improved_score,
                                                original_missing, improved_missing)
    pdf_buffer = create_pdf(improved_resume)
    pdf_base64 = base64.b64encode(pdf_buffer).decode('utf-8')
    return jsonify({
        "improved_resume": improved_resume,
        "original_evaluation": original_evaluation,
        "improved_evaluation": improved_evaluation,
        "progress": progress_data,
        "pdf_base64": pdf_base64
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000) # Run the Flask app on port 5000
