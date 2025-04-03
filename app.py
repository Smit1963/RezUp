def create_pdf(resume_text):
    """Create PDF using ReportLab with proper Unicode support"""
    buffer = io.BytesIO()
    
    # Get default stylesheet
    styles = getSampleStyleSheet()
    
    # Only add styles if they don't exist
    if 'Center' not in styles:
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
    
    if 'SectionHeader' not in styles:
        styles.add(ParagraphStyle(name='SectionHeader', 
                                fontName='Helvetica-Bold',
                                fontSize=14,
                                spaceAfter=12))
    
    # Use existing BodyText style instead of redefining
    body_style = styles['BodyText']
    body_style.spaceAfter = 6  # Just modify the spacing we need
    
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
    
