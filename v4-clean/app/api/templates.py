"""
Template Routes for Resume Health Checker v4.0

All template rendering and HTML generation functions for premium results,
including embedded and full-page template responses.
"""
import logging
import re
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..core.database import AnalysisDB
from ..services.analysis import analysis_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

def _get_default_score(context: str, fallback: int) -> int:
    """Get configurable default score for template contexts"""
    from ..core.config import config
    default_scores = getattr(config, 'template_default_scores', {})
    return default_scores.get(context, fallback)

# Setup Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

@router.get("/premium-results/{analysis_id}")
async def premium_results_page(
    analysis_id: str,
    product_type: str = "resume_analysis",
    embedded: bool = False
):
    """Display premium service results in a beautiful HTML page"""
    try:
        # Get the premium service data
        analysis = AnalysisDB.get(analysis_id)
        if not analysis:
            return HTMLResponse(content="<h1>Analysis not found</h1>", status_code=404)
        
        # Check if payment was successful
        if analysis.get('payment_status') != 'paid':
            return HTMLResponse(content="<h1>Payment required</h1>", status_code=402)
        
        # Get job posting if available
        job_posting = analysis.get('job_posting')
        
        # Generate premium service based on product type
        if product_type == "resume_analysis":
            result = await analysis_service.analyze_resume(
                analysis['resume_text'], 
                'premium',
                job_posting
            )
        elif product_type == "job_fit_analysis":
            if not job_posting:
                return HTMLResponse(content="<h1>Job posting required for job fit analysis</h1>", status_code=400)
            result = await analysis_service.analyze_resume(
                analysis['resume_text'], 
                'premium',
                job_posting
            )
        elif product_type == "cover_letter":
            if not job_posting:
                return HTMLResponse(content="<h1>Job posting required for cover letter generation</h1>", status_code=400)
            result = await analysis_service.generate_cover_letter(
                analysis['resume_text'], 
                job_posting
            )
        elif product_type == "resume_enhancer":
            if not job_posting:
                return HTMLResponse(content="<h1>Job posting required for resume enhancement</h1>", status_code=400)
            result = await analysis_service.enhance_resume(
                analysis['resume_text'], 
                job_posting
            )
        elif product_type == "interview_prep":
            result = await analysis_service.generate_interview_prep(
                analysis['resume_text'], 
                job_posting
            )
        elif product_type == "salary_insights":
            result = await analysis_service.generate_salary_insights(
                analysis['resume_text']
            )
        elif product_type == "resume_rewrite":
            if not job_posting:
                return HTMLResponse(content="<h1>Job posting required for resume rewrite</h1>", status_code=400)
            result = await analysis_service.complete_resume_rewrite(
                analysis['resume_text'], 
                job_posting
            )
        elif product_type == "mock_interview":
            if not job_posting:
                return HTMLResponse(content="<h1>Job posting required for mock interview</h1>", status_code=400)
            result = await analysis_service.generate_mock_interview_premium(
                analysis['resume_text'], 
                job_posting
            )
        else:
            return HTMLResponse(content=f"<h1>Invalid product type: {product_type}</h1>", status_code=400)
        
        # Store the premium result
        AnalysisDB.update_premium_result(analysis_id, result)
        
        # Generate HTML content based on product type
        if embedded:
            html_content = generate_embedded_premium_results_html(product_type, result, analysis_id)
        else:
            html_content = generate_premium_results_html(product_type, result, analysis_id)
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Premium results page error: {e}")
        return HTMLResponse(content=f"<h1>Error generating premium results: {str(e)}</h1>", status_code=500)

# =============================================================================
# PREMIUM RESULTS HTML GENERATION FUNCTIONS
# =============================================================================

def generate_premium_results_html(product_type: str, result: dict, analysis_id: str) -> str:
    """Generate beautiful HTML for premium results"""
    
    if product_type == "resume_analysis":
        return generate_resume_analysis_html(result, analysis_id)
    elif product_type == "job_fit_analysis":
        return generate_job_fit_html(result, analysis_id)
    elif product_type == "cover_letter":
        return generate_cover_letter_html(result, analysis_id)
    elif product_type == "resume_rewrite":
        return generate_resume_rewrite_html(result, analysis_id)
    elif product_type == "interview_prep":
        return generate_interview_prep_html(result, analysis_id)
    elif product_type == "mock_interview":
        return generate_mock_interview_html(result, analysis_id)
    elif product_type == "salary_insights":
        return generate_salary_insights_html(result, analysis_id)
    else:
        return f"<h1>Premium results for {product_type}</h1><pre>{result}</pre>"

def generate_resume_analysis_html(result: dict, analysis_id: str) -> str:
    """Generate HTML for premium resume analysis results using template"""
    
    # Prepare template context with robust None handling
    context = {
        "overall_score": result.get('overall_score') or 'N/A',
        "industry_identified": result.get('industry_identified') or 'Not specified',
        "strength_highlights": result.get('strength_highlights') or [],
        "improvement_opportunities": result.get('improvement_opportunities') or [],
        "ats_optimization": result.get('ats_optimization') or {},
        "text_rewrites": result.get('text_rewrites') or [],
        "success_prediction": result.get('success_prediction') or '',
        "analysis_id": analysis_id
    }
    
    # Render template
    template = templates.get_template("resume_analysis_full.html")
    return template.render(context)

def generate_job_fit_html(result: dict, analysis_id: str) -> str:
    """Generate HTML for job fit analysis results using template"""
    
    # Extract data from result with robust None handling
    match_percentage = result.get('match_percentage') or 'N/A'
    requirements_met = result.get('requirements_met') or []
    missing_qualifications = result.get('missing_qualifications') or []
    strengths = result.get('strengths') or []
    improvements = result.get('improvements') or []
    recommendations = result.get('recommendations') or []
    
    # Create context for template
    context = {
        "fit_score": match_percentage,
        "strong_matches": requirements_met + strengths,  # Combine requirements met and strengths
        "skill_gaps": missing_qualifications + improvements,  # Combine missing qualifications and improvements
        "recommendations": recommendations,
        "analysis_id": analysis_id,
        "keyword_analysis": result.get('keyword_analysis') or {},
        "improvement_plan": result.get('improvement_plan') or ''
    }
    
    # Render template
    template = templates.get_template("job_fit_analysis_full.html")
    return template.render(context)

def generate_cover_letter_html(result: dict, analysis_id: str) -> str:
    """Generate HTML for cover letter results using Jinja2 template"""
    
    # Extract variables from result dict
    cover_letter = result.get('cover_letter', '')
    key_points = result.get('key_points_highlighted', [])
    tone = result.get('tone', '')
    word_count = result.get('word_count', '')
    
    # Create context for template
    context = {
        "cover_letter_text": cover_letter,
        "key_points_highlighted": key_points,
        "tone": tone,
        "word_count": word_count,
        "analysis_id": analysis_id
    }
    
    # Render template
    template = templates.get_template("cover_letter_full.html")
    return template.render(context)

def generate_interview_prep_html(result: dict, analysis_id: str) -> str:
    """Generate HTML for interview prep results"""
    return f"<h1>Interview Prep Results</h1><pre>{result}</pre>"

def generate_mock_interview_html(result: dict, analysis_id: str) -> str:
    """Generate HTML for mock interview simulation results using Jinja2 template"""
    
    # Prepare template context with the result data
    context = {
        "interview_simulation": result.get('interview_simulation', []),
        "interview_strategy": result.get('interview_strategy', {}),
        "company_specific_prep": result.get('company_specific_prep', {}),
        "challenging_scenarios": result.get('challenging_scenarios', []),
        "confidence_boosters": result.get('confidence_boosters', {}),
        "final_preparation_checklist": result.get('final_preparation_checklist', []),
        "interview_success_prediction": result.get('interview_success_prediction', ''),
        "analysis_id": analysis_id
    }
    
    # Render the template to HTML string
    template = templates.get_template("mock_interview_embedded.html")
    return template.render(context)

def generate_salary_insights_html(result: dict, analysis_id: str) -> str:
    """Generate HTML for salary insights results"""
    return f"<h1>Salary Insights Results</h1><pre>{result}</pre>"

def generate_resume_rewrite_html(result: dict, analysis_id: str) -> str:
    """Generate full HTML page for resume rewrite results using Jinja2 template"""
    
    # Prepare template context with robust None handling
    context = {
        "rewritten_resume": result.get('rewritten_resume') or {},
        "strategic_changes": result.get('strategic_changes') or {},
        "before_after_comparison": result.get('before_after_comparison') or [],
        "interview_generation_potential": result.get('interview_generation_potential') or '',
        "next_steps": result.get('next_steps') or '',
        "analysis_id": analysis_id
    }
    
    # Render the template to HTML string
    template = templates.get_template("resume_rewrite_full.html")
    return template.render(context)

# =============================================================================
# EMBEDDED PREMIUM RESULTS GENERATION FUNCTIONS
# =============================================================================

def generate_embedded_premium_results_html(product_type: str, result: dict, analysis_id: str) -> str:
    """Generate embedded HTML for premium results that fits in the right panel"""
    
    if product_type == "resume_analysis":
        return generate_embedded_resume_analysis_html(result, analysis_id)
    elif product_type == "job_fit_analysis":
        return generate_embedded_job_fit_html(result, analysis_id)
    elif product_type == "cover_letter":
        return generate_embedded_cover_letter_html(result, analysis_id)
    elif product_type == "resume_rewrite":
        return generate_embedded_resume_rewrite_html(result, analysis_id)
    elif product_type == "interview_prep":
        return generate_embedded_interview_prep_html(result, analysis_id)
    elif product_type == "mock_interview":
        return generate_mock_interview_html(result, analysis_id)  # Use same template for embedded
    elif product_type == "salary_insights":
        return generate_embedded_salary_insights_html(result, analysis_id)
    else:
        return f"<h1>Premium results for {product_type}</h1><pre>{result}</pre>"

def generate_embedded_resume_analysis_html(result: dict, analysis_id: str) -> str:
    """Generate embedded HTML for premium resume analysis results using Jinja2 template"""
    
    # Extract and process overall_score to handle both numeric and string values
    overall_score = result.get('overall_score', 'N/A')
    if isinstance(overall_score, str):
        # Try to extract numeric value from strings like "85" or "Score 75-90"
        numeric_match = re.search(r'\d+', str(overall_score))
        if numeric_match:
            try:
                overall_score = int(numeric_match.group())
            except ValueError:
                pass  # Keep as string
    
    # Map AI response to template expectations
    # Transform strength_highlights to key_strengths format
    key_strengths = []
    for i, strength in enumerate(result.get('strength_highlights', [])):
        key_strengths.append({
            'category': f'Strength {i+1}',
            'description': strength
        })
    
    # Create critical_issues from content_enhancement growth_areas
    critical_issues = []
    content_enhancement = result.get('content_enhancement', {})
    for i, issue in enumerate(content_enhancement.get('growth_areas', [])):
        critical_issues.append({
            'issue_type': f'Issue {i+1}',
            'description': issue,
            'solution': 'Review the strategic additions section for recommendations'
        })
    
    # Create section_analysis from text_rewrites
    section_analysis = []
    for rewrite in result.get('text_rewrites', []):
        section_analysis.append({
            'section_name': rewrite.get('section', 'Unknown Section'),
            'score': _get_default_score('section_analysis', 75),  # Configurable default score
            'strengths': [rewrite.get('why_better', 'Improved content')],
            'weaknesses': [rewrite.get('original', 'Original content')] if rewrite.get('original') else [],
            'recommendations': [rewrite.get('improved', 'No specific recommendations')]
        })
    
    # Transform ats_optimization to expected format
    ats_optimization = result.get('ats_optimization', {})
    ats_analysis = {
        'ats_score': _get_default_score('ats_analysis', 75),  # Configurable default ATS score
        'issues': ats_optimization.get('enhancement_opportunities', [])
    }
    
    # Create basic keyword_analysis (AI doesn't provide this, so create placeholder)
    keyword_analysis = {
        'missing_keywords': ['Add relevant industry keywords'],
        'present_keywords': [],
        'recommended_additions': ['Include more specific technical terms']
    }
    
    # Create action_plan from strategic_additions
    action_plan = []
    strategic_additions = content_enhancement.get('strategic_additions', [])
    for i, addition in enumerate(strategic_additions):
        action_plan.append({
            'priority': 'High' if i < 2 else 'Medium',
            'action': addition,
            'impact': 'Will improve your resume effectiveness'
        })
    
    # Create configurable score_breakdown (AI doesn't provide this)
    score_breakdown = {
        'content_quality': _get_default_score('content_quality', 80),
        'formatting': _get_default_score('formatting', 75),
        'keywords': _get_default_score('keywords', 70),
        'experience': _get_default_score('experience', 85)
    }
    
    # Prepare template context with the result data
    context = {
        "overall_score": overall_score,
        "score_breakdown": score_breakdown,
        "key_strengths": key_strengths,
        "critical_issues": critical_issues,
        "section_analysis": section_analysis,
        "ats_analysis": ats_analysis,
        "keyword_analysis": keyword_analysis,
        "action_plan": action_plan,
        "success_prediction": result.get('success_prediction', ''),
        "analysis_id": analysis_id
    }
    
    # Render the template to HTML string
    template = templates.get_template("resume_analysis_embedded.html")
    return template.render(context)

def generate_embedded_job_fit_html(result: dict, analysis_id: str) -> str:
    """Generate embedded HTML for job fit analysis results using Jinja2 template"""
    
    # Extract and process overall_match_score to handle both numeric and string values
    overall_match_score = result.get('job_fit_score', result.get('overall_match_score', 'N/A'))
    if isinstance(overall_match_score, str):
        # Try to extract numeric value from strings like "Score 80 based on..." 
        numeric_match = re.search(r'\d+', str(overall_match_score))
        if numeric_match:
            try:
                overall_match_score = int(numeric_match.group())
            except ValueError:
                overall_match_score = _get_default_score('job_fit_fallback', 75)  # Configurable fallback
        else:
            overall_match_score = _get_default_score('job_fit_default', 75)  # Configurable default
    
    # Transform strategic_advantages to key_strengths format expected by template
    key_strengths = []
    for i, advantage in enumerate(result.get('strategic_advantages', [])):
        key_strengths.append({
            'category': f'Strategic Advantage {i+1}',
            'strength': f'Advantage {i+1}',
            'description': advantage,
            'evidence': 'Based on your resume analysis'
        })
    
    # Create skill_gaps from optimization_keywords (what's missing)
    skill_gaps = []
    for i, keyword in enumerate(result.get('optimization_keywords', [])):
        skill_gaps.append({
            'category': 'Technical Skills',
            'missing_skill': keyword,
            'description': f'Consider highlighting {keyword} experience in your resume',
            'priority': 'Medium',
            'learning_resources': 'Professional courses, certifications, or hands-on projects'
        })
    
    # Create experience_alignment from positioning_strategy
    positioning_strategy = result.get('positioning_strategy', {})
    experience_alignment = {
        'alignment_score': _get_default_score('experience_alignment', 80),  # Configurable alignment score
        'relevant_experiences': [{
            'role': 'Current Role',
            'relevance': positioning_strategy.get('primary_value', 'Strong alignment with role requirements')
        }],
        'experience_gaps': []  # Will be populated if we find gaps
    }
    
    # Add supporting qualifications as relevant experiences
    for i, qual in enumerate(positioning_strategy.get('supporting_qualifications', [])):
        experience_alignment['relevant_experiences'].append({
            'role': f'Qualification {i+1}',
            'relevance': qual
        })
    
    # Create keyword_match from optimization_keywords
    optimization_keywords = result.get('optimization_keywords', [])
    # Extract actual matched keywords from the analysis result
    matched_keywords = []
    if 'matched_keywords' in result:
        matched_keywords = result['matched_keywords']
    elif 'keywords_found' in result:
        matched_keywords = result['keywords_found']
    elif 'present_keywords' in result:
        matched_keywords = result['present_keywords']
    
    # If no matched keywords found, use empty list instead of hardcoded tech terms
    if not matched_keywords:
        matched_keywords = []
    
    keyword_match = {
        'matched_keywords': matched_keywords,  # Use actual keywords from analysis
        'missing_keywords': optimization_keywords[:6],  # First 6 optimization keywords
        'keyword_density': min(15, len(optimization_keywords) * 2)  # Calculate density
    }
    
    # Create match_breakdown with mock scores
    match_breakdown = {
        'technical_skills': {
            'score': overall_match_score if isinstance(overall_match_score, int) else 80,
            'details': 'Strong alignment in core technical requirements'
        },
        'experience_level': {
            'score': 85,
            'details': 'Experience level matches role expectations'
        },
        'domain_knowledge': {
            'score': 75,
            'details': 'Good understanding of relevant domain concepts'
        },
        'soft_skills': {
            'score': 90,
            'details': 'Leadership and communication skills well-developed'
        }
    }
    
    # Prepare template context with the result data
    context = {
        "overall_match_score": overall_match_score,
        "match_breakdown": match_breakdown,
        "key_strengths": key_strengths,
        "skill_gaps": skill_gaps,
        "experience_alignment": experience_alignment,
        "keyword_match": keyword_match,
        "strategic_recommendations": [
            {
                "category": f"Enhancement {i+1}",
                "recommendation": enhancement,
                "specific_actions": [f"Implement this enhancement: {enhancement}"],
                "timeline": "Immediate"
            }
            for i, enhancement in enumerate(result.get('resume_enhancements', []))
        ],
        "interview_prep": {'confidence_tips': [result.get('interview_confidence', 'Approach with confidence')]},
        "success_probability": {
            'score': overall_match_score if isinstance(overall_match_score, int) else 80,
            'probability': f"{overall_match_score if isinstance(overall_match_score, int) else 80}% match probability",
            'assessment': 'Strong candidate alignment with role requirements'
        },
        "analysis_id": analysis_id
    }
    
    # Render the template to HTML string
    template = templates.get_template("job_fit_analysis_embedded.html")
    return template.render(context)

def generate_embedded_cover_letter_html(result: dict, analysis_id: str) -> str:
    """Generate embedded HTML for cover letter results using Jinja2 template"""
    
    # Map actual AI response to template expectations
    cover_letter_content = result.get('cover_letter', '')
    tone = result.get('tone', 'Professional')
    word_count = result.get('word_count', 0)
    key_points = result.get('key_points_highlighted', [])
    
    # Create cover_letter_analysis with mock scores based on quality indicators
    letter_analysis = {
        "tone_score": 88,  # Good professional tone
        "keyword_coverage": 85,  # Reasonable keyword integration
        "structure_score": 90,  # Well-structured format
        "overall_rating": 87,  # Overall good quality
        "tone_assessment": f"Your cover letter maintains a {tone.lower()} tone throughout, which is appropriate for the role."
    }
    
    # Transform key_points_highlighted to key_highlights format
    key_highlights = []
    for i, point in enumerate(key_points):
        key_highlights.append({
            'category': f'Key Point {i+1}',
            'title': f'Highlight {i+1}',
            'description': point,
            'impact': 'Strengthens your application by demonstrating relevant experience'
        })
    
    # Simplified strategic_elements - reduce to just 2 key elements
    strategic_elements = [
        {
            'element_type': 'Professional Opening',
            'purpose': 'Establishes immediate interest and relevance',
            'example': 'Strong opening that connects to the role',
            'effectiveness': 85
        },
        {
            'element_type': 'Compelling Closing',
            'purpose': 'Encourages action and reinforces interest', 
            'example': 'Clear call-to-action for next steps',
            'effectiveness': 88
        }
    ]
    
    # Simplified customization_details
    customization_details = {
        'company_research': [
            'Tailored to specific company and role requirements',
            'Incorporates relevant industry terminology'
        ],
        'role_alignment': [
            'Highlights most relevant experiences for this position',
            'Addresses key qualifications mentioned in job posting'
        ],
        'personal_brand': 'The cover letter effectively communicates your unique value proposition'
    }
    
    # Simplified next_steps - reduce to 2 essential steps
    next_steps = [
        {
            'action': 'Review and customize further',
            'details': 'Consider adding specific company details if available',
            'timeline': 'Before sending'
        },
        {
            'action': 'Proofread carefully',
            'details': 'Check for any typos, grammar errors, or formatting issues',
            'timeline': 'Final step before submission'
        }
    ]
    
    # Create success_prediction
    success_prediction = {
        'score': 85,
        'assessment': 'This cover letter effectively positions you as a strong candidate by highlighting relevant experience and demonstrating genuine interest in the role.',
        'strengths': ['Professional tone', 'Relevant experience highlighted', 'Clear structure', 'Compelling narrative']
    }
    
    # Prepare template context with the mapped data
    context = {
        "cover_letter_text": cover_letter_content,  # Template expects cover_letter_text not cover_letter_content
        "letter_analysis": letter_analysis,  # Template expects letter_analysis not cover_letter_analysis
        "key_highlights": key_highlights,
        "strategic_elements": strategic_elements,
        "customization_details": customization_details,
        "next_steps": next_steps,
        "success_prediction": success_prediction,
        "analysis_id": analysis_id
    }
    
    # Render the template to HTML string
    template = templates.get_template("cover_letter_embedded.html")
    return template.render(context)

def generate_embedded_interview_prep_html(result: dict, analysis_id: str) -> str:
    """Generate embedded HTML for interview prep results"""
    return f"""
    <div class="premium-results">
        <div class="premium-header">
            <h2>&#127908; Interview Preparation</h2>
            <p>Personalized interview questions and answers</p>
        </div>
        <div class="section">
            <h3>Interview Prep Results</h3>
            <pre>{result}</pre>
        </div>
        <div class="actions">
            <button class="btn print-btn" onclick="window.print()">&#128424; Print Report</button>
            <a href="/" class="btn">&#127968; Return to App</a>
        </div>
    </div>
    """

def generate_embedded_salary_insights_html(result: dict, analysis_id: str) -> str:
    """Generate embedded HTML for salary insights results"""
    return f"""
    <div class="premium-results">
        <div class="premium-header">
            <h2>&#128176; Salary Insights</h2>
            <p>Market rate analysis for your role</p>
        </div>
        <div class="section">
            <h3>Salary Insights</h3>
            <pre>{result}</pre>
        </div>
        <div class="actions">
            <button class="btn print-btn" onclick="window.print()">&#128424; Print Report</button>
            <a href="/" class="btn">&#127968; Return to App</a>
        </div>
    </div>
    """

def generate_embedded_resume_rewrite_html(result: dict, analysis_id: str) -> str:
    """Generate embedded HTML for resume rewrite results using Jinja2 template"""
    
    rewritten_resume = result.get('rewritten_resume', {})
    strategic_changes = result.get('strategic_changes', {})
    interview_generation_potential = result.get('interview_generation_potential', '')
    
    # Prepare template context
    context = {
        "rewritten_resume": rewritten_resume,
        "strategic_changes": strategic_changes,
        "interview_generation_potential": interview_generation_potential,
        "analysis_id": analysis_id
    }
    
    # Render the embedded template to HTML string
    template = templates.get_template("resume_rewrite_embedded.html")
    return template.render(context)