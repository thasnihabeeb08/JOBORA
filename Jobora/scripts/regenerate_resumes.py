import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobora.settings')
django.setup()

from users.models import UserProfile
from django.core.files.base import ContentFile
import random

# Skills by job role
SKILLS_BY_ROLE = {
    'Data Scientist': ['Python', 'R', 'SQL', 'Machine Learning', 'TensorFlow', 'PyTorch', 'Data Visualization', 'Statistics', 'Pandas', 'NumPy'],
    'UI/UX Designer': ['Figma', 'Adobe XD', 'Sketch', 'User Research', 'Wireframing', 'Prototyping', 'Usability Testing', 'Interaction Design'],
    'Frontend Developer (React)': ['React', 'JavaScript', 'TypeScript', 'HTML5', 'CSS3', 'Redux', 'Webpack', 'Jest', 'Responsive Design'],
    'Cloud Architect': ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform', 'Cloud Security', 'DevOps', 'CI/CD'],
    'Backend Developer (Python)': ['Python', 'Django', 'Flask', 'PostgreSQL', 'MongoDB', 'REST APIs', 'GraphQL', 'Redis', 'Celery'],
}

def regenerate_resume(profile):
    """Generate a better resume with actual skills"""
    username = profile.user.username
    full_name = profile.user.get_full_name() or username
    
    # Determine role based on skills or default
    skills_list = []
    if profile.skills:
        skills_list = [s.strip() for s in profile.skills.split(',') if s.strip()]
    
    # If no skills, assign random ones
    if not skills_list:
        # Try to match to a role
        for role, role_skills in SKILLS_BY_ROLE.items():
            if role.lower() in profile.current_role.lower() if profile.current_role else '':
                skills_list = role_skills
                break
        if not skills_list:
            # Default skills
            skills_list = ['Python', 'JavaScript', 'SQL', 'Communication', 'Problem Solving']
    
    skills_text = '\n• '.join(skills_list[:8])
    
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
Experienced professional with expertise in {', '.join(skills_list[:3])}. 
Proven track record of delivering high-quality results and solving complex problems.

TECHNICAL SKILLS
---------------
• {skills_text}

WORK EXPERIENCE
--------------
• {profile.years_experience or 3}+ years of professional experience
• Developed and maintained multiple web applications
• Collaborated with cross-functional teams
• Implemented best practices and coding standards

EDUCATION
---------
• {profile.get_highest_education_display() if profile.highest_education else "Bachelor's Degree"}
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
    print("🔄 REGENERATING RESUMES FOR ALL USERS")
    print("=" * 60)
    
    profiles = UserProfile.objects.all()
    total = profiles.count()
    print(f"\n📊 Found {total} user profiles\n")
    
    updated = 0
    errors = 0
    
    for i, profile in enumerate(profiles, 1):
        try:
            print(f"🔄 [{i}/{total}] Processing: {profile.user.username}")
            
            # Create new resume
            resume_file = regenerate_resume(profile)
            
            # Save to profile
            profile.resume.save(f"resume_{profile.user.username}.txt", resume_file, save=True)
            print(f"   ✅ Resume regenerated")
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