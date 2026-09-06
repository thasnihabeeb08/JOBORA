import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobora.settings')
django.setup()

from users.models import UserProfile
from jobs.models import Job
from django.core.files.base import ContentFile
import random

# Skills by job role based on actual jobs
JOB_SKILLS = {}
for job in Job.objects.all():
    if job.skills_required:
        skills = [s.strip().lower() for s in job.skills_required.split(',') if s.strip()]
        JOB_SKILLS[job.title.lower()] = skills

def generate_skills_for_profile(profile):
    """Generate skills based on user's applications or random"""
    all_skills = set()
    
    # Get skills from jobs this user applied to
    applications = profile.user.applications.all()
    for app in applications:
        if app.job.skills_required:
            skills = [s.strip().lower() for s in app.job.skills_required.split(',') if s.strip()]
            all_skills.update(skills)
    
    # If no skills from jobs, add some default IT skills
    if not all_skills:
        all_skills = {'python', 'java', 'sql', 'communication', 'teamwork', 'problem solving'}
    
    return list(all_skills)[:8]  # Return top 8 skills

def regenerate_resume_with_skills(profile):
    """Generate a proper resume with skills section"""
    username = profile.user.username
    full_name = profile.user.get_full_name() or username
    
    # Generate skills
    skills_list = generate_skills_for_profile(profile)
    skills_text = '\n• '.join(skills_list)
    
    resume_content = f"""
====================================================================
                         PROFESSIONAL RESUME
====================================================================

PERSONAL INFORMATION
--------------------
Name: {full_name}
Email: {profile.user.email}
Phone: {profile.phone or '+91 9876543210'}
Location: {profile.location or 'India'}

PROFESSIONAL SUMMARY
-------------------
Experienced IT professional with expertise in {', '.join(skills_list[:3])}. 
Proven track record of delivering high-quality solutions and working in team environments.

TECHNICAL SKILLS
---------------
• {skills_text}

WORK EXPERIENCE
--------------
• {profile.years_experience or 3}+ years of professional experience
• Developed and maintained multiple software applications
• Collaborated with cross-functional teams
• Implemented best practices and coding standards
• Solved complex technical problems
• Communicated effectively with stakeholders

EDUCATION
---------
• {profile.get_highest_education_display() if profile.highest_education else "Bachelor's Degree in Computer Science"}
• {profile.institution or 'University Name'}
• {profile.graduation_year or '2020'}

CERTIFICATIONS
--------------
• Professional Development Certificate
• Technical Skills Certification

LANGUAGES
--------
• English (Fluent)
• Hindi (Native)

====================================================================
"""
    return ContentFile(resume_content.encode('utf-8'), name=f"resume_{username}.txt")

def run():
    print("=" * 60)
    print("🔄 FIXING RESUMES WITH PROPER SKILLS")
    print("=" * 60)
    
    profiles = UserProfile.objects.all()
    total = profiles.count()
    print(f"\n📊 Found {total} user profiles\n")
    
    updated = 0
    errors = 0
    
    for i, profile in enumerate(profiles, 1):
        try:
            print(f"🔄 [{i}/{total}] Processing: {profile.user.username}")
            
            # Generate skills for this profile
            skills = generate_skills_for_profile(profile)
            print(f"   📝 Skills: {', '.join(skills[:5])}...")
            
            # Create new resume
            resume_file = regenerate_resume_with_skills(profile)
            
            # Save to profile
            profile.resume.save(f"resume_{profile.user.username}.txt", resume_file, save=True)
            print(f"   ✅ Resume updated with {len(skills)} skills")
            updated += 1
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")
            errors += 1
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"✅ Updated: {updated} profiles")
    print(f"❌ Errors: {errors}")
    print("=" * 60)

if __name__ == "__main__":
    run()