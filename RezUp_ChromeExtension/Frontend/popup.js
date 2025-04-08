document.addEventListener('DOMContentLoaded', function() {
  const jobDescriptionInput = document.getElementById('jobDescription');
  const resumeFileInput = document.getElementById('resumeFile');
  const evaluateBtn = document.getElementById('evaluateBtn');
  const skillsBtn = document.getElementById('skillsBtn');
  const keywordsBtn = document.getElementById('keywordsBtn');
  const scoreBtn = document.getElementById('scoreBtn');
  const generateBtn = document.getElementById('generateBtn');
  const responseContainer = document.getElementById('responseContainer');
  const responseText = document.getElementById('responseText');
  const progressContainer = document.getElementById('progressContainer');
  const progressBarFill = document.getElementById('progressBarFill');
  const progressText = document.getElementById('progressText');
  const downloadContainer = document.getElementById('downloadContainer');
  const downloadLink = document.getElementById('downloadLink');

  const backendUrl = 'http://127.0.0.1:5000'; // Your Flask backend URL

  function showResponse(data) {
    responseContainer.style.display = 'block';
    responseText.textContent = JSON.stringify(data, null, 2);
    progressContainer.style.display = 'none';
    downloadContainer.style.display = 'none';
  }

  function showProgress(message, percentage) {
    progressContainer.style.display = 'block';
    progressText.textContent = message;
    progressBarFill.style.width = `${percentage}%`;
  }

  function handleButtonClick(endpoint) {
    const jobDescription = jobDescriptionInput.value;
    const resumeFile = resumeFileInput.files[0];

    if (!jobDescription || !resumeFile) {
      alert('Please enter the job description and upload your resume.');
      return;
    }

    const formData = new FormData();
    formData.append('job_description', jobDescription);
    formData.append('resume', resumeFile);

    showProgress(`Processing...`, 50); // Show some initial progress

    fetch(`${backendUrl}/${endpoint}`, {
      method: 'POST',
      body: formData,
    })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        alert(`Error: ${data.error}`);
        progressContainer.style.display = 'none';
        responseContainer.style.display = 'none';
        downloadContainer.style.display = 'none';
      } else {
        showResponse(data);
        if (data.score !== undefined) {
          progressText.textContent = `Current Match: ${data.score}%`;
          progressBarFill.style.width = `${data.score}%`;
        }
      }
    })
    .catch(error => {
      alert(`There was an error: ${error}`);
      progressContainer.style.display = 'none';
      responseContainer.style.display = 'none';
      downloadContainer.style.display = 'none';
    });
  }

  evaluateBtn.addEventListener('click', () => handleButtonClick('evaluate'));
  skillsBtn.addEventListener('click', () => handleButtonClick('skills'));
  keywordsBtn.addEventListener('click', () => handleButtonClick('keywords'));
  scoreBtn.addEventListener('click', () => handleButtonClick('score'));

  generateBtn.addEventListener('click', () => {
    const jobDescription = jobDescriptionInput.value;
    const resumeFile = resumeFileInput.files[0];

    if (!jobDescription || !resumeFile) {
      alert('Please enter the job description and upload your resume.');
      return;
    }

    const formData = new FormData();
    formData.append('job_description', jobDescription);
    formData.append('resume', resumeFile);

    showProgress(`Generating Improved Resume...`, 75);

    fetch(`${backendUrl}/generate`, {
      method: 'POST',
      body: formData,
    })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        alert(`Error: ${data.error}`);
        progressContainer.style.display = 'none';
        responseContainer.style.display = 'none';
        downloadContainer.style.display = 'none';
      } else {
        responseContainer.style.display = 'block';
        responseText.textContent = data.improved_resume;
        progressContainer.style.display = 'none';
        downloadContainer.style.display = 'block';
        const pdfBase64 = data.pdf_base64;
        downloadLink.href = 'data:application/pdf;base64,' + pdfBase64;
      }
    })
    .catch(error => {
      alert(`There was an error: ${error}`);
      progressContainer.style.display = 'none';
      responseContainer.style.display = 'none';
      downloadContainer.style.display = 'none';
    });
  });
});
