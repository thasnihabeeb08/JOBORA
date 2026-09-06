# jobs/matching.py
from users.models import UserProfile

def calculate_application_match(application):
    """Permanent matching function"""
    job = application.job
    
    try:
        profile = UserProfile.objects.get(user=application.candidate)
    except UserProfile.DoesNotExist:
        return {
            'score': 0,
            'skills_match': 0,
            'experience_match': 0,
            'location_match': 0,
            'education_match': 0,
            'job_type_match': 0,
            'skills_found': [],
            'skills_missing': []
        }
    
    score = 0
    breakdown = {}
    
    # 1. Skills Match (40%)
    if job.skills_required and profile.skills:
        job_skills = set(s.strip().lower() for s in job.skills_required.split(',') if s.strip())
        candidate_skills = set(s.strip().lower() for s in profile.skills.split(',') if s.strip())
        
        if job_skills:
            skills_match = len(job_skills.intersection(candidate_skills)) / len(job_skills)
            skills_match_score = skills_match * 40
            score += skills_match_score
            breakdown['skills_match'] = round(skills_match_score, 1)
            breakdown['skills_found'] = list(job_skills.intersection(candidate_skills))[:5]
            breakdown['skills_missing'] = list(job_skills - candidate_skills)[:5]
    
    # 2. Experience Match (20%)
    experience_years = profile.years_experience or 0
    
    # Map experience_level to years
    exp_map = {'entry_level': 0, 'mid_level': 2, 'senior_level': 5, 'executive': 8}
    required_years = exp_map.get(job.experience_level, 0)
    
    if required_years == 0:
        experience_score = 15  # Entry level jobs
    elif experience_years >= required_years:
        experience_score = 20
    else:
        experience_ratio = min(experience_years / required_years, 1)
        experience_score = experience_ratio * 20
    
    score += experience_score
    breakdown['experience_match'] = round(experience_score, 1)
    
    # 3. Location Match (15%)
    if profile.location:
        if job.location and profile.location.lower() == job.location.lower():
            location_score = 15
        elif job.is_remote:
            location_score = 12
        else:
            location_score = 5
    else:
        location_score = 5
    
    score += location_score
    breakdown['location_match'] = round(location_score, 1)
    
    # 4. Education Match (15%)
    if profile.highest_education and job.education_required:
        if profile.highest_education.lower() in job.education_required.lower():
            education_score = 15
        else:
            education_score = 5
    else:
        education_score = 10
    
    score += education_score
    breakdown['education_match'] = round(education_score, 1)
    
    # 5. Job Type Match (10%)
    if profile.preferred_job_types and job.job_type:
        if job.job_type.lower() in profile.preferred_job_types.lower():
            job_type_score = 10
        else:
            job_type_score = 3
    else:
        job_type_score = 5
    
    score += job_type_score
    breakdown['job_type_match'] = round(job_type_score, 1)
    
    # Final score
    final_score = min(max(score, 0), 100)
    breakdown['score'] = round(final_score, 1)
    
    return breakdown