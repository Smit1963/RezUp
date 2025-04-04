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

            # Get progress data (without the unwanted sections)
            progress_data = evaluate_resume_progress(original_score, improved_score,
                                                   original_missing, improved_missing)

            # Display results - simplified version
            st.markdown('<h2 class="sub-header">✨ Optimization Results</h2>', unsafe_allow_html=True)

            # Score comparison visualization
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"Original Score: {progress_data['original_score']}%")
            with col2:
                st.success(f"Optimized Score: {progress_data['optimized_score']}%")
            with col3:
                st.info(f"Improvement: +{progress_data['improvement']}%")

            # Show recovered keywords if any
            if progress_data['recovered_keywords']:
                st.success(f"Recovered keywords: {', '.join(progress_data['recovered_keywords'])}")

            # Show remaining missing keywords if any
            if progress_data['remaining_missing']:
                st.warning(f"Still missing: {', '.join(progress_data['remaining_missing'])}")

            with st.expander("📝 Original Resume Evaluation"):
                st.markdown(f'<div class="response-container">{original_evaluation}</div>', unsafe_allow_html=True)

            with st.expander("🆕 Optimized Resume"):
                st.markdown(f'<div class="response-container">{improved_resume}</div>', unsafe_allow_html=True)

            with st.expander("🔍 Optimized Resume Evaluation"):
                st.markdown(f'<div class="response-container">{improved_evaluation}</div>', unsafe_allow_html=True)

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
