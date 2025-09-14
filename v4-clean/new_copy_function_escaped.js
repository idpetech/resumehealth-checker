        function copyResumeText() {{
            // Extract text content from all resume sections
            let resumeText = '';
            
            // Professional Summary
            const summaryText = document.querySelector('.rewritten-content')?.textContent;
            if (summaryText) {{
                resumeText += 'PROFESSIONAL SUMMARY\n' + summaryText.trim() + '\n\n';
            }}
            
            // Core Competencies
            const competencies = Array.from(document.querySelectorAll('.strengths-list li')).map(li => li.textContent.trim());
            if (competencies.length > 0) {{
                resumeText += 'CORE COMPETENCIES\n' + competencies.map(c => '• ' + c).join('\n') + '\n\n';
            }}
            
            // Professional Experience
            const experienceItems = document.querySelectorAll('.experience-preview, .experience-item');
            if (experienceItems.length > 0) {{
                resumeText += 'PROFESSIONAL EXPERIENCE\n';
                experienceItems.forEach(item => {{
                    const header = item.querySelector('h4, .experience-header')?.textContent?.trim();
                    if (header) {{
                        resumeText += header + '\n';
                    }}
                    const bullets = Array.from(item.querySelectorAll('.bullet-list li, .bullet-points li')).map(li => li.textContent.trim());
                    bullets.forEach(bullet => {{
                        resumeText += '• ' + bullet + '\n';
                    }});
                    resumeText += '\n';
                }});
            }}
            
            // Education (if present)
            const education = document.querySelector('.resume-section h3')?.nextElementSibling?.textContent?.trim();
            if (education) {{
                resumeText += 'EDUCATION\n' + education + '\n\n';
            }}
            
            // Copy to clipboard
            if (resumeText.trim()) {{
                navigator.clipboard.writeText(resumeText.trim()).then(() => {{
                    alert('Complete resume copied to clipboard!');
                }}).catch(err => {{
                    console.error('Failed to copy: ', err);
                    alert('Failed to copy to clipboard. Please try again.');
                }});
            }} else {{
                alert('No resume content found to copy.');
            }}
        }}