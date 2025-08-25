// Resume Health Checker - Main Application JavaScript

let selectedFile = null;
let currentAnalysis = null;

// Check for payment success token in URL
const urlParams = new URLSearchParams(window.location.search);
const paymentToken = urlParams.get('payment_token');

// Handle file upload
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        selectedFile = file;
        document.getElementById('analyzeBtn').disabled = false;
        
        // Update upload UI to show selected file
        const uploadDiv = document.querySelector('.file-upload');
        uploadDiv.innerHTML = `
            <div class="upload-text">
                <strong>Selected: ${file.name}</strong><br>
                <small>Click to change file</small>
            </div>
        `;
    }
}

// Drag and drop functionality
const fileUpload = document.querySelector('.file-upload');

fileUpload.addEventListener('dragover', (e) => {
    e.preventDefault();
    fileUpload.classList.add('dragover');
});

fileUpload.addEventListener('dragleave', () => {
    fileUpload.classList.remove('dragover');
});

fileUpload.addEventListener('drop', (e) => {
    e.preventDefault();
    fileUpload.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        const file = files[0];
        if (file.type === 'application/pdf' || file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
            selectedFile = file;
            document.getElementById('fileInput').files = files;
            handleFileSelect({ target: { files: [file] } });
        } else {
            alert('Please upload a PDF or Word document');
        }
    }
});

async function analyzeResume() {
    if (!selectedFile) {
        alert('Please select a file first');
        return;
    }

    const resultsSection = document.getElementById('resultsSection');
    resultsSection.style.display = 'block';
    resultsSection.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Analyzing your resume...</p>
        </div>
    `;

    const formData = new FormData();
    formData.append('file', selectedFile);
    
    // Add payment token if present (for paid analysis)
    if (paymentToken) {
        formData.append('payment_token', paymentToken);
    }

    try {
        const response = await fetch(getApiUrl('checkResume'), {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const analysis = await response.json();
        currentAnalysis = analysis;
        
        // DEBUG: Log the full analysis to browser console
        console.log('=== FULL ANALYSIS RESPONSE ===');
        console.log(analysis);
        console.log('================================');
        
        displayResults(analysis);

    } catch (error) {
        resultsSection.innerHTML = `
            <div style="color: #f44336; text-align: center; padding: 2rem;">
                <h3>Analysis Failed</h3>
                <p>Something went wrong. Please try again.</p>
                <small>Error: ${error.message}</small>
            </div>
        `;
    }
}

function displayResults(analysis) {
    const resultsSection = document.getElementById('resultsSection');
    const score = parseInt(analysis.overall_score);
    const scoreClass = getScoreClass(score);

    // Debug logging
    console.log('Analysis type:', analysis.analysis_type);
    console.log('Has text_rewrites:', 'text_rewrites' in analysis);
    console.log('Has sample_improvements:', 'sample_improvements' in analysis);
    if (analysis.text_rewrites) {
        console.log('Number of rewrites:', analysis.text_rewrites.length);
    }

    if (analysis.analysis_type === 'free') {
        // Display free analysis with upgrade prompt
        resultsSection.innerHTML = `
            <div style="text-align: center;">
                <div class="score-circle ${scoreClass}">
                    ${score}/100
                </div>
                <h2>Your Resume Health Score</h2>
                <p style="margin: 1rem 0; color: #666;">Here are the major issues we found:</p>
            </div>
            
            <div style="margin: 2rem 0;">
                <h3 style="color: #ff6b6b; margin-bottom: 1rem;">Major Issues Found:</h3>
                <ul class="issues-list">
                    ${analysis.major_issues.map(issue => `<li>${issue}</li>`).join('')}
                </ul>
            </div>

            <div class="upgrade-section">
                <h3>Want the Complete Analysis?</h3>
                <p>${analysis.teaser_message}</p>
                <p style="margin: 1rem 0;">Get detailed feedback on:</p>
                <ul style="text-align: left; max-width: 400px; margin: 1rem auto;">
                    <li>✓ ATS optimization recommendations</li>
                    <li>✓ Content clarity improvements</li>
                    <li>✓ Impact metrics suggestions</li>
                    <li>✓ Formatting fixes</li>
                    <li>✓ Prioritized action plan</li>
                </ul>
                <a href="${STRIPE_CONFIG.paymentUrl}?success_url=${encodeURIComponent(window.location.origin + '/?payment_token=' + STRIPE_CONFIG.successToken)}" class="upgrade-btn">
                    Unlock Full Report - $5
                </a>
            </div>
        `;
    } else {
        // Display detailed paid analysis
        resultsSection.innerHTML = `
            <div style="text-align: center;">
                <div class="score-circle ${scoreClass}">
                    ${score}/100
                </div>
                <h2>🎯 Complete Resume Analysis</h2>
                <p style="margin: 1rem 0; color: #666;">Comprehensive breakdown with actionable improvements</p>
            </div>

            <!-- Free Analysis Recap -->
            <div style="background: #f0f8ff; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #2196F3; margin: 2rem 0;">
                <h3 style="color: #1976D2; margin-bottom: 1rem;">📋 Key Issues Summary</h3>
                <ul style="margin: 0; padding-left: 1rem;">
                    ${analysis.major_issues.map(issue => `<li style="margin-bottom: 0.5rem;">${issue}</li>`).join('')}
                </ul>
            </div>

            <div class="detailed-results">
                <div class="metric-card">
                    <div class="metric-score">${analysis.ats_optimization.score}/100</div>
                    <h3>ATS Optimization</h3>
                    <h4>Issues:</h4>
                    <ul>
                        ${analysis.ats_optimization.issues.map(issue => `<li>${issue}</li>`).join('')}
                    </ul>
                    <h4>Improvements:</h4>
                    <ul>
                        ${analysis.ats_optimization.improvements.map(imp => `<li>${imp}</li>`).join('')}
                    </ul>
                </div>

                <div class="metric-card">
                    <div class="metric-score">${analysis.content_clarity.score}/100</div>
                    <h3>Content Clarity</h3>
                    <h4>Issues:</h4>
                    <ul>
                        ${analysis.content_clarity.issues.map(issue => `<li>${issue}</li>`).join('')}
                    </ul>
                    <h4>Improvements:</h4>
                    <ul>
                        ${analysis.content_clarity.improvements.map(imp => `<li>${imp}</li>`).join('')}
                    </ul>
                </div>

                <div class="metric-card">
                    <div class="metric-score">${analysis.impact_metrics.score}/100</div>
                    <h3>Impact Metrics</h3>
                    <h4>Issues:</h4>
                    <ul>
                        ${analysis.impact_metrics.issues.map(issue => `<li>${issue}</li>`).join('')}
                    </ul>
                    <h4>Improvements:</h4>
                    <ul>
                        ${analysis.impact_metrics.improvements.map(imp => `<li>${imp}</li>`).join('')}
                    </ul>
                </div>

                <div class="metric-card">
                    <div class="metric-score">${analysis.formatting.score}/100</div>
                    <h3>Formatting</h3>
                    <h4>Issues:</h4>
                    <ul>
                        ${analysis.formatting.issues.map(issue => `<li>${issue}</li>`).join('')}
                    </ul>
                    <h4>Improvements:</h4>
                    <ul>
                        ${analysis.formatting.improvements.map(imp => `<li>${imp}</li>`).join('')}
                    </ul>
                </div>
            </div>

            <!-- Text Rewrites Section -->
            ${analysis.text_rewrites && analysis.text_rewrites.length > 0 ? `
                <div style="background: #f8f9fa; padding: 2rem; border-radius: 12px; margin: 2rem 0; border-left: 4px solid #28a745;">
                    <h3 style="color: #155724; margin-bottom: 1.5rem;">✨ Ready-to-Use Text Improvements</h3>
                    ${analysis.text_rewrites.map((rewrite, index) => `
                        <div style="background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <h4 style="color: #495057; margin-bottom: 1rem;">📝 ${rewrite.section}</h4>
                            
                            <div style="margin-bottom: 1rem;">
                                <strong style="color: #dc3545;">❌ Current:</strong>
                                <div style="background: #fff5f5; padding: 0.8rem; border-radius: 4px; margin: 0.5rem 0; font-style: italic; border-left: 3px solid #dc3545;">
                                    "${rewrite.original}"
                                </div>
                            </div>
                            
                            <div style="margin-bottom: 1rem;">
                                <strong style="color: #28a745;">✅ Improved:</strong>
                                <div style="background: #f0fff4; padding: 0.8rem; border-radius: 4px; margin: 0.5rem 0; border-left: 3px solid #28a745;">
                                    "${rewrite.improved}"
                                </div>
                            </div>
                            
                            <div style="font-size: 0.9rem; color: #6c757d; font-style: italic;">
                                💡 <strong>Why this works:</strong> ${rewrite.explanation}
                            </div>
                        </div>
                    `).join('')}
                </div>
            ` : ''}

            <!-- Sample Bullet Improvements -->
            ${analysis.sample_improvements ? `
                <div style="background: #e8f5e8; padding: 2rem; border-radius: 12px; margin: 2rem 0; border-left: 4px solid #4CAF50;">
                    <h3 style="color: #2e7d32; margin-bottom: 1.5rem;">🎯 Bullet Point Makeover Examples</h3>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 1rem;">
                        <div>
                            <h4 style="color: #d32f2f; margin-bottom: 1rem;">❌ Weak Bullets</h4>
                            ${analysis.sample_improvements.weak_bullets.map(bullet => `
                                <div style="background: #fff; padding: 1rem; border-radius: 4px; margin-bottom: 0.5rem; border-left: 3px solid #d32f2f;">
                                    • ${bullet}
                                </div>
                            `).join('')}
                        </div>
                        
                        <div>
                            <h4 style="color: #388e3c; margin-bottom: 1rem;">✅ Strong Bullets</h4>
                            ${analysis.sample_improvements.strong_bullets.map(bullet => `
                                <div style="background: #fff; padding: 1rem; border-radius: 4px; margin-bottom: 0.5rem; border-left: 3px solid #388e3c;">
                                    • ${bullet}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            ` : ''}

            <div class="recommendations">
                <h3>🎯 Top Priority Action Plan</h3>
                <ol>
                    ${analysis.top_recommendations.map(rec => `<li>${rec}</li>`).join('')}
                </ol>
            </div>
            
            <div style="background: #e3f2fd; padding: 1.5rem; border-radius: 8px; text-align: center; margin-top: 2rem;">
                <h4 style="color: #1565c0; margin-bottom: 0.5rem;">🚀 Ready to Implement?</h4>
                <p style="color: #424242; margin: 0;">Copy the improved text above and update your resume to increase your interview rate!</p>
            </div>
        `;
    }
}

function getScoreClass(score) {
    if (score >= 80) return 'score-excellent';
    if (score >= 60) return 'score-good';
    if (score >= 40) return 'score-fair';
    return 'score-poor';
}

// If payment token is present, automatically analyze the previously uploaded resume
if (paymentToken && selectedFile) {
    analyzeResume();
}