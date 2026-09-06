import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobora.settings')
django.setup()

from jobs.models import Application
from users.models import UserProfile
from ai.matcher import ResumeJobMatcher
from django.core.files.base import ContentFile
import random

def fix_application(app):
    """Update profile to match job requirements"""
    try:
        profile = app.candidate.profile
        job = app.job
        
        print(f"\n📝 Fixing: {app.candidate.username} - {job.title}")
        
        # 1. Update experience to match job level
        if job.experience_level:
            if 'fresher' in job.experience_level.lower():
                profile.years_experience = random.randint(0, 1)
            elif 'junior' in job.experience_level.lower() or '1-3' in job.experience_level:
                profile.years_experience = random.randint(1, 3)
            elif 'mid' in job.experience_level.lower() or '3-6' in job.experience_level:
                profile.years_experience = random.randint(3, 6)
            elif 'senior' in job.experience_level.lower() or '6-10' in job.experience_level:
                profile.years_experience = random.randint(6, 10)
            elif 'executive' in job.experience_level.lower() or '10+' in job.experience_level:
                profile.years_experience = random.randint(10, 15)
        
        # 2. Update location to match job
        if job.location and not job.is_remote:
            profile.location = job.location
        else:
            profile.location = "Remote"
        
        # 3. Update preferred job types
        profile.preferred_job_types = job.job_type
        
        # 4. Update skills to include job requirements
        job_skills = []
        if job.skills_required:
            job_skills = [s.strip() for s in job.skills_required.split(',') if s.strip()]
        
        # Add some matching skills
        profile.skills = ', '.join(job_skills[:8])
        
        profile.save()
        
        # 5. Update resume with matching skills
        resume_content = f"""
====================================================================
                         PROFESSIONAL RESUME
====================================================================

PERSONAL INFORMATION
--------------------
Name: {profile.user.get_full_name() or profile.user.username}
Email: {profile.user.email}
Location: {profile.location}

PROFESSIONAL SUMMARY
-------------------
Experienced professional seeking {job.title} position. Strong background in {', '.join(job_skills[:3])}.

TECHNICAL SKILLS
---------------
• {'\n• '.join(job_skills[:10])}

WORK EXPERIENCE
--------------
• {profile.years_experience}+ years of experience
• Developed and maintained software applications
• Collaborated with teams to deliver projects
• Solved complex technical problems

EDUCATION
---------
• Bachelor's Degree
• University
• 2020

====================================================================
"""
        
        resume_file = ContentFile(resume_content.encode('utf-8'), 
                                 name=f"resume_{profile.user.username}.txt")
        profile.resume.save(f"resume_{profile.user.username}.txt", resume_file, save=True)
        
        # Recalculate score
        matcher = ResumeJobMatcher()
        scores = matcher.calculate_final_score(app)
        
        print(f"   ✅ New match score: {scores['percentage']}%")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def run():
    print("=" * 60)
    print("🔧 FIXING ALL APPLICATIONS")
    print("=" * 60)
    
    # Get applications with low scores
    apps = Application.objects.filter(match_percentage__lt=50)[:100]  # Process 100 at a time
    total = apps.count()
    print(f"\n📊 Found {total} applications to fix\n")
    
    fixed = 0
    for i, app in enumerate(apps, 1):
        print(f"\n🔄 [{i}/{total}]", end="")
        if fix_application(app):
            fixed += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Fixed {fixed} applications")
    print("=" * 60)

if __name__ == "__main__":
    run()