import random
import string
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.base import ContentFile
import os

# Import models
from users.models import UserProfile, SavedJob
from jobs.models import Company, Job, Application, Message, Interview

# ============================================
# CONFIGURATION
# ============================================
NUM_JOB_SEEKERS = 30
APPLICATION_STATUS = 'applied'

# ============================================
# INDIAN NAMES DATA
# ============================================
FIRST_NAMES = [
    'Aarav', 'Vihaan', 'Vivaan', 'Ananya', 'Diya', 'Advik', 'Kabir', 'Aaradhya',
    'Reyansh', 'Sai', 'Arjun', 'Ishaan', 'Anaya', 'Anvi', 'Rudra', 'Saanvi',
    'Dhruv', 'Aryan', 'Yash', 'Atharv', 'Laksh', 'Aadhya', 'Krishna', 'Tanvi',
    'Rohan', 'Rahul', 'Amit', 'Priya', 'Neha', 'Raj', 'Pooja', 'Sanjay',
    'Vikram', 'Deepak', 'Sunita', 'Anita', 'Rajesh', 'Suresh', 'Nisha', 'Kavita',
    'Mohit', 'Ravi', 'Sneha', 'Divya', 'Karthik', 'Swati', 'Nikhil', 'Meera',
]

LAST_NAMES = [
    'Sharma', 'Verma', 'Patel', 'Kumar', 'Singh', 'Reddy', 'Gupta', 'Joshi',
    'Chatterjee', 'Mukherjee', 'Banerjee', 'Nair', 'Menon', 'Iyer', 'Rao',
    'Desai', 'Patil', 'Shinde', 'Yadav', 'Jha', 'Sinha', 'Das', 'Bose',
    'Malhotra', 'Mehra', 'Kohli', 'Kapoor', 'Khanna', 'Chopra', 'Thakur',
]

# ============================================
# INDIAN CITIES
# ============================================
CITIES = [
    'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Kolkata',
    'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow', 'Kanpur', 'Nagpur',
    'Indore', 'Bhopal', 'Visakhapatnam', 'Patna', 'Vadodara',
    'Kochi', 'Thiruvananthapuram', 'Kozhikode', 'Mysore', 'Mangalore',
]

# ============================================
# SKILLS
# ============================================
ALL_SKILLS = [
    'Python', 'Java', 'JavaScript', 'React', 'Django', 'Node.js', 'SQL',
    'AWS', 'Docker', 'Kubernetes', 'MongoDB', 'Angular', 'Vue.js', 'TypeScript',
    'C++', 'C#', 'PHP', 'Ruby on Rails', 'Flask', 'FastAPI', 'GraphQL',
    'DevOps', 'CI/CD', 'Jenkins', 'Terraform', 'Ansible', 'Linux',
    'Communication', 'Team Leadership', 'Project Management', 'Time Management',
    'Problem Solving', 'Critical Thinking', 'Microsoft Office', 'Google Suite',
    'Customer Service', 'Sales', 'Negotiation', 'Public Speaking',
    'Data Analysis', 'Research', 'Writing', 'Editing', 'Multitasking'
]

# ============================================
# INSTITUTIONS
# ============================================
INSTITUTIONS = [
    'IIT Bombay', 'IIT Delhi', 'IIT Madras', 'IIT Kanpur', 'IIT Kharagpur',
    'NIT Trichy', 'NIT Surathkal', 'BITS Pilani', 'DTU Delhi', 'NSIT Delhi',
    'Anna University', 'Jadavpur University', 'University of Mumbai',
    'Delhi University', 'Christ University', 'Manipal University',
    'VIT Vellore', 'SRM University', 'KIIT University', 'Amity University',
]

# ============================================
# HELPER FUNCTIONS
# ============================================

def random_phone():
    """Generate a random Indian phone number"""
    return f"+91 {random.randint(6,9)}{random.randint(0,9)}{random.randint(0,9)}-{random.randint(10000,99999)}"

def random_date_of_birth():
    """Generate a random date of birth (20-40 years old)"""
    today = timezone.now().date()
    years = random.randint(20, 40)
    return today - timedelta(days=years*365 + random.randint(0, 365))

def random_graduation_year():
    """Generate a random graduation year (2010-2024)"""
    return random.randint(2010, 2024)

def random_years_experience():
    """Generate random years of experience (0-15)"""
    return random.randint(0, 15)

def random_salary():
    """Generate random expected salary (3-30 lakhs)"""
    return random.randint(300000, 3000000)

def random_skills(count=8):
    """Generate random skills"""
    return ', '.join(random.sample(ALL_SKILLS, min(count, len(ALL_SKILLS))))

def random_bio(name):
    """Generate a random professional bio"""
    templates = [
        f"{name} is a passionate professional with experience in technology and innovation.",
        f"{name} loves solving complex problems and creating impactful solutions.",
        f"{name} is dedicated to continuous learning and professional growth.",
        f"{name} has a strong track record of delivering high-quality work.",
    ]
    return random.choice(templates)

def random_cover_letter(job_title, company_name, candidate_name):
    """Generate a random cover letter"""
    templates = [
        f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company_name}. With my background and skills, I believe I would be a valuable addition to your team.

Thank you for considering my application.

Best regards,
{candidate_name}""",
        f"""Dear Hiring Team,

I was thrilled to see the opening for {job_title} at {company_name}. Your company's reputation for innovation aligns perfectly with my professional goals.

I would welcome the opportunity to discuss my qualifications further.

Sincerely,
{candidate_name}"""
    ]
    return random.choice(templates)

def create_dummy_resume(username, full_name):
    """Create a simple text file as resume"""
    resume_content = f"""
====================================================================
                         RESUME
====================================================================

PERSONAL INFORMATION
--------------------
Name: {full_name}
Email: {username}@example.com
Phone: {random_phone()}
Location: {random.choice(CITIES)}

EDUCATION
---------
• Bachelor's Degree
• Institution: {random.choice(INSTITUTIONS)}
• Year: {random_graduation_year()}

SKILLS
------
{random_skills(10)}

====================================================================
    """
    return ContentFile(resume_content.encode('utf-8'), name=f"resume_{username}.txt")

# ============================================
# MAIN SEEDING FUNCTION
# ============================================

def run():
    print("\n" + "="*70)
    print("🚀 STARTING DATABASE SEEDING")
    print("="*70)
    
    # Get all existing companies and jobs
    companies = list(Company.objects.all())
    jobs = list(Job.objects.filter(is_active=True))
    
    print(f"\n📊 Existing Data:")
    print(f"   - Companies found: {len(companies)}")
    print(f"   - Active jobs found: {len(jobs)}")
    
    if not companies or not jobs:
        print("\n❌ ERROR: No companies or jobs found in database!")
        print("   Please add companies and jobs first before running this script.")
        return
    
    # Track created users
    created_users = []
    login_credentials = []
    
    print(f"\n👥 Creating {NUM_JOB_SEEKERS} job seekers...")
    print("-" * 70)
    
    for i in range(NUM_JOB_SEEKERS):
        # Generate random name
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        username = f"{first_name.lower()}{last_name.lower()}{random.randint(1,99)}"
        email = f"{username}@example.com"
        password = "password123"
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            created_users.append(user)
            
            # Determine user type
            user_type = random.choice(['fresher', 'experienced'])
            years_exp = random_years_experience() if user_type == 'experienced' else 0
            
            # Create profile
            profile = UserProfile.objects.create(
                user=user,
                phone=random_phone(),
                location=random.choice(CITIES),
                date_of_birth=random_date_of_birth(),
                headline=f"{random.choice(['Experienced', 'Skilled', 'Passionate'])} {random.choice(['Developer', 'Designer', 'Engineer', 'Analyst'])}",
                summary=random_bio(first_name),
                user_type=user_type,
                highest_education=random.choice(['bachelors', 'masters']),
                field_of_study=random.choice(['Computer Science', 'Information Technology', 'Business Administration']),
                institution=random.choice(INSTITUTIONS),
                graduation_year=random_graduation_year(),
                years_experience=years_exp,
                current_role=f"{random.choice(['Junior', 'Senior', 'Lead'])} {random.choice(['Developer', 'Designer', 'Engineer'])}" if years_exp > 0 else "",
                current_company=random.choice(companies).name if years_exp > 0 and random.choice([True, False]) else "",
                skills=random_skills(12),
                preferred_job_types=','.join(random.sample(['full_time', 'part_time', 'internship'], random.randint(1, 3))),
                preferred_locations=','.join(random.sample(CITIES, random.randint(1, 3))),
                salary_expectation=random_salary(),
                portfolio_link=f"https://{username}.portfolio.com" if random.choice([True, False]) else "",
                github_profile=f"https://github.com/{username}" if random.choice([True, False]) else "",
                linkedin_profile=f"https://linkedin.com/in/{username}" if random.choice([True, False]) else "",
                availability_status=random.choice(['immediate', '2_weeks', '1_month']),
                work_preference=random.choice(['office', 'hybrid', 'remote']),
                willing_to_relocate=random.choice([True, False]),
                job_search_intensity=random.choice(['casual', 'active', 'urgent']),
                is_profile_complete=True,
            )
            
            # Create resume file
            try:
                full_name = f"{first_name} {last_name}"
                resume_content = create_dummy_resume(username, full_name)
                profile.resume.save(f"resume_{username}.txt", resume_content, save=True)
                print(f"   ✅ Resume created for {username}")
            except Exception as e:
                print(f"   ⚠️ Could not create resume for {username}: {e}")
            
            profile.save()
            
            # Store login credentials
            login_credentials.append({
                'name': f"{first_name} {last_name}",
                'username': username,
                'email': email,
                'password': password
            })
            
            print(f"   ✅ Created: {first_name} {last_name} ({username})")
            
        except Exception as e:
            print(f"   ❌ Error creating user {username}: {e}")
    
    print(f"\n✅ Created {len(created_users)} job seekers successfully!")
    
    # ============================================
    # CREATE APPLICATIONS WITH RESUMES - FIXED
    # ============================================
    print(f"\n📝 Creating applications with resumes...")
    print("-" * 70)
    
    total_jobs = len(jobs)
    jobs_with_applications = set()
    applications_count = 0
    
    # First, ensure every job gets at least one application
    print(f"\n   Ensuring every job has at least one application...")
    for job in jobs:
        if created_users:
            seeker = random.choice(created_users)
            
            if not Application.objects.filter(job=job, candidate=seeker).exists():
                try:
                    full_name = f"{seeker.first_name} {seeker.last_name}"
                    
                    # IMPORTANT: Get profile to access resume
                    profile = UserProfile.objects.get(user=seeker)
                    
                    # Create application WITH resume
                    Application.objects.create(
                        job=job,
                        candidate=seeker,
                        resume=profile.resume,  # CRITICAL: This adds the resume
                        status=APPLICATION_STATUS,
                        cover_letter=random_cover_letter(job.title, job.company.name, full_name),
                        expected_salary=random_salary(),
                        applied_on=timezone.now() - timedelta(days=random.randint(1, 30))
                    )
                    applications_count += 1
                    jobs_with_applications.add(job.id)
                    print(f"   ✅ {seeker.username} applied to {job.title[:30]}...")
                except Exception as e:
                    print(f"   ❌ Error creating application: {e}")
    
    # Then, create additional random applications
    print(f"\n   Creating additional random applications...")
    additional_apps = NUM_JOB_SEEKERS * 3
    
    for i in range(additional_apps):
        if created_users and jobs:
            seeker = random.choice(created_users)
            job = random.choice(jobs)
            
            if not Application.objects.filter(job=job, candidate=seeker).exists():
                try:
                    full_name = f"{seeker.first_name} {seeker.last_name}"
                    
                    # IMPORTANT: Get profile to access resume
                    profile = UserProfile.objects.get(user=seeker)
                    
                    # Create application WITH resume
                    Application.objects.create(
                        job=job,
                        candidate=seeker,
                        resume=profile.resume,  # CRITICAL: This adds the resume
                        status=APPLICATION_STATUS,
                        cover_letter=random_cover_letter(job.title, job.company.name, full_name),
                        expected_salary=random_salary(),
                        applied_on=timezone.now() - timedelta(days=random.randint(1, 30))
                    )
                    applications_count += 1
                    jobs_with_applications.add(job.id)
                    
                    if i % 10 == 0:
                        print(f"   ✅ Created {i+1} additional applications...")
                        
                except Exception as e:
                    print(f"   ❌ Error creating additional application: {e}")
    
    print(f"\n✅ Created {applications_count} total applications with resumes!")
    print(f"   Jobs with applications: {len(jobs_with_applications)}/{total_jobs}")
    
    # ============================================
    # DISPLAY LOGIN CREDENTIALS
    # ============================================
    print("\n" + "="*70)
    print("🔐 LOGIN CREDENTIALS FOR ALL JOB SEEKERS")
    print("="*70)
    print(f"\n{'Name':<25} {'Username':<20} {'Email':<30} {'Password':<15}")
    print("-" * 90)
    
    for cred in login_credentials:
        print(f"{cred['name']:<25} {cred['username']:<20} {cred['email']:<30} {cred['password']:<15}")
    
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    print(f"✅ Total Job Seekers Created: {len(created_users)}")
    print(f"✅ Total Applications Created: {applications_count}")
    print(f"🏢 Total Companies: {len(companies)}")
    print(f"💼 Total Jobs: {len(jobs)}")
    print(f"📝 Jobs with Applications: {len(jobs_with_applications)}/{len(jobs)}")
    print("\n✨ All passwords are: password123")
    print("="*70)

# Execute the function
run()