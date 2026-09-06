# populate_data.py - COMPLETE FIXED VERSION WITH UNIQUE PASSWORDS
import os
import sys
import django
import random
import secrets
import string
from django.utils import timezone
from datetime import timedelta

# Setup Django
sys.path.append('C:/Users/dell/jobora')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobora.settings')
django.setup()

from django.contrib.auth.models import User
from users.models import Company
from jobs.models import JobCategory, Job, CompanyAnalytics

# ==================== PASSWORD GENERATION ====================
def generate_company_password(company_name):
    """Generate unique, secure password for each company"""
    # Clean company name for password
    clean_name = company_name.split()[0].upper()  # First word in uppercase
    
    # Get initials (first 3 letters)
    if len(clean_name) >= 3:
        base = clean_name[:3]
    else:
        base = clean_name.ljust(3, 'X')
    
    # Special characters
    special_chars = ['@', '#', '$', '!', '&', '*', '%', '^']
    special = random.choice(special_chars)
    
    # Random 3-digit number
    numbers = ''.join(secrets.choice(string.digits) for _ in range(3))
    
    # Format: Base + Year + Special + Numbers
    password = f"{base}2024{special}{numbers}"
    
    return password

def create_or_update_company_users():
    """Create/update all company users with UNIQUE passwords"""
    print("\n🔐 SETTING UNIQUE PASSWORDS FOR ALL COMPANIES:")
    print("=" * 50)
    
    company_credentials = {}
    
    # List of all companies with their details
    companies_list = [
        # IT Companies
        {
            'username': 'infosys_hr', 'email': 'hr@infosys.com',
            'first_name': 'Ravi', 'last_name': 'Kumar',
            'name': 'Infosys Limited', 'contact_person': 'Ravi Kumar',
            'phone': '9876500001', 'location': 'Bangalore, Karnataka',
            'industry': 'it', 'is_approved': True,
        },
        {
            'username': 'tcs_recruiter', 'email': 'careers@tcs.com',
            'first_name': 'Rajesh', 'last_name': 'Gopinathan',
            'name': 'Tata Consultancy Services', 'contact_person': 'Rajesh Gopinathan',
            'phone': '9876500002', 'location': 'Mumbai, Maharashtra',
            'industry': 'it', 'is_approved': True,
        },
        {
            'username': 'wipro_hiring', 'email': 'hiring@wipro.com',
            'first_name': 'Thierry', 'last_name': 'Delaporte',
            'name': 'Wipro Technologies', 'contact_person': 'Thierry Delaporte',
            'phone': '9876500003', 'location': 'Bangalore, Karnataka',
            'industry': 'it', 'is_approved': True,
        },
        {
            'username': 'hcl_tech', 'email': 'careers@hcl.com',
            'first_name': 'Vijay', 'last_name': 'Kumar',
            'name': 'HCL Technologies', 'contact_person': 'Vijay Kumar',
            'phone': '9876500004', 'location': 'Noida, Uttar Pradesh',
            'industry': 'it', 'is_approved': True,
        },
        {
            'username': 'tech_mahindra', 'email': 'hiring@techmahindra.com',
            'first_name': 'CP', 'last_name': 'Gurnani',
            'name': 'Tech Mahindra', 'contact_person': 'CP Gurnani',
            'phone': '9876500005', 'location': 'Pune, Maharashtra',
            'industry': 'it', 'is_approved': True,
        },
        
        # E-commerce & Startups
        {
            'username': 'flipkart_careers', 'email': 'careers@flipkart.com',
            'first_name': 'Kalyan', 'last_name': 'Krishnamurthy',
            'name': 'Flipkart', 'contact_person': 'Kalyan Krishnamurthy',
            'phone': '9876500006', 'location': 'Bangalore, Karnataka',
            'industry': 'ecommerce', 'is_approved': True,
        },
        {
            'username': 'zomato_hr', 'email': 'hr@zomato.com',
            'first_name': 'Deepinder', 'last_name': 'Goyal',
            'name': 'Zomato', 'contact_person': 'Deepinder Goyal',
            'phone': '9876500007', 'location': 'Gurgaon, Haryana',
            'industry': 'food_delivery', 'is_approved': True,
        },
        {
            'username': 'swiggy_hiring', 'email': 'hiring@swiggy.com',
            'first_name': 'Sriharsha', 'last_name': 'Majety',
            'name': 'Swiggy', 'contact_person': 'Sriharsha Majety',
            'phone': '9876500008', 'location': 'Bangalore, Karnataka',
            'industry': 'food_delivery', 'is_approved': True,
        },
        
        # Banking & Finance
        {
            'username': 'hdfc_bank', 'email': 'careers@hdfcbank.com',
            'first_name': 'Sashidhar', 'last_name': 'Jagdishan',
            'name': 'HDFC Bank', 'contact_person': 'Sashidhar Jagdishan',
            'phone': '9876500009', 'location': 'Mumbai, Maharashtra',
            'industry': 'banking', 'is_approved': True,
        },
        {
            'username': 'icici_bank', 'email': 'hr@icicibank.com',
            'first_name': 'Sandeep', 'last_name': 'Bakhshi',
            'name': 'ICICI Bank', 'contact_person': 'Sandeep Bakhshi',
            'phone': '9876500010', 'location': 'Mumbai, Maharashtra',
            'industry': 'banking', 'is_approved': True,
        },
        
        # Healthcare
        {
            'username': 'apollo_hospitals', 'email': 'careers@apollohospitals.com',
            'first_name': 'Sangita', 'last_name': 'Reddy',
            'name': 'Apollo Hospitals', 'contact_person': 'Sangita Reddy',
            'phone': '9876500011', 'location': 'Chennai, Tamil Nadu',
            'industry': 'healthcare', 'is_approved': True,
        },
        {
            'username': 'fortis_healthcare', 'email': 'hiring@fortishealthcare.com',
            'first_name': 'Ashutosh', 'last_name': 'Raghuvanshi',
            'name': 'Fortis Healthcare', 'contact_person': 'Ashutosh Raghuvanshi',
            'phone': '9876500012', 'location': 'Gurgaon, Haryana',
            'industry': 'healthcare', 'is_approved': True,
        },
        
        # Manufacturing
        {
            'username': 'tata_motors', 'email': 'recruitment@tatamotors.com',
            'first_name': 'Shailesh', 'last_name': 'Chandra',
            'name': 'Tata Motors', 'contact_person': 'Shailesh Chandra',
            'phone': '9876500013', 'location': 'Mumbai, Maharashtra',
            'industry': 'manufacturing', 'is_approved': True,
        },
        {
            'username': 'mahindra_group', 'email': 'hr@mahindra.com',
            'first_name': 'Anish', 'last_name': 'Shah',
            'name': 'Mahindra Group', 'contact_person': 'Anish Shah',
            'phone': '9876500014', 'location': 'Mumbai, Maharashtra',
            'industry': 'manufacturing', 'is_approved': True,
        },
        
        # Education & Retail
        {
            'username': 'byjus_learning', 'email': 'careers@byjus.com',
            'first_name': 'Byju', 'last_name': 'Raveendran',
            'name': "Byju's", 'contact_person': 'Byju Raveendran',
            'phone': '9876500015', 'location': 'Bangalore, Karnataka',
            'industry': 'education', 'is_approved': True,
        },
        {
            'username': 'amazon_india', 'email': 'hiring@amazon.in',
            'first_name': 'Amit', 'last_name': 'Agarwal',
            'name': 'Amazon India', 'contact_person': 'Amit Agarwal',
            'phone': '9876500016', 'location': 'Bangalore, Karnataka',
            'industry': 'ecommerce', 'is_approved': True,
        },
        {
            'username': 'reliance_retail', 'email': 'careers@relianceretail.com',
            'first_name': 'Mukesh', 'last_name': 'Ambani',
            'name': 'Reliance Retail', 'contact_person': 'Mukesh Ambani',
            'phone': '9876500017', 'location': 'Mumbai, Maharashtra',
            'industry': 'retail', 'is_approved': True,
        },
        
        # Test Company
        {
            'username': 'test_company', 'email': 'test@company.com',
            'first_name': 'Test', 'last_name': 'Company',
            'name': 'Test Company', 'contact_person': 'Test Manager',
            'phone': '9876512345', 'location': 'Delhi, Delhi',
            'industry': 'it', 'is_approved': True,
        },
    ]
    
    # Create/Update each company
    for i, data in enumerate(companies_list, 1):
        # Generate UNIQUE password
        password = generate_company_password(data['name'])
        
        # Get or create user
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'email': data['email'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'is_staff': False,
                'is_active': True
            }
        )
        
        # SET UNIQUE PASSWORD (always update)
        user.set_password(password)
        user.save()
        
        # Get or create company
        company, company_created = Company.objects.get_or_create(
            user=user,
            defaults={
                'name': data['name'],
                'contact_person': data['contact_person'],
                'phone': data['phone'],
                'location': data['location'],
                'industry': data['industry'],
                'is_approved': data['is_approved']
            }
        )
        
        # Store credentials
        company_credentials[data['name']] = {
            'username': data['username'],
            'password': password,
            'email': data['email']
        }
        
        action = "Created" if company_created else "Updated"
        print(f"✅ {i:2d}. {action} {data['name']:<30}")
        print(f"      Username: {data['username']}")
        print(f"      Password: {password}")
    
    # Save credentials to file
    save_credentials_to_file(company_credentials)
    
    print("=" * 50)
    print(f"🎯 Created/Updated {len(companies_list)} companies with UNIQUE passwords!")
    return True

def save_credentials_to_file(credentials):
    """Save company credentials to a secure file"""
    filename = "company_credentials_SECURE.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("JOBORA - COMPANY LOGIN CREDENTIALS (SECURE)\n")
        f.write("=" * 60 + "\n")
        f.write("IMPORTANT: Each company has a UNIQUE password!\n")
        f.write("Generated: " + timezone.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
        f.write("=" * 60 + "\n\n")
        
        for company_name, creds in credentials.items():
            f.write(f"🏢 {company_name}\n")
            f.write("-" * 50 + "\n")
            f.write(f"Username: {creds['username']}\n")
            f.write(f"Password: {creds['password']}\n")
            f.write(f"Email:    {creds['email']}\n")
            f.write("-" * 50 + "\n\n")
    
    print(f"📁 Credentials saved to: {filename}")
    print("⚠️  Keep this file secure! Do NOT commit to Git.")

# ==================== JOB CREATION ====================
def clear_existing_data():
    """Remove all existing jobs and analytics"""
    print("\n🧹 Clearing existing jobs and analytics...")
    Job.objects.all().delete()
    CompanyAnalytics.objects.all().delete()
    print("✅ All jobs and analytics cleared")

def create_job_categories():
    """Create job categories if not exists"""
    categories = [
        {'name': 'Information Technology', 'description': 'IT jobs'},
        {'name': 'Healthcare', 'description': 'Medical jobs'},
        {'name': 'Finance & Banking', 'description': 'Banking jobs'},
        {'name': 'Business & Management', 'description': 'Management jobs'},
        {'name': 'Engineering', 'description': 'Engineering jobs'},
        {'name': 'Design & Creative', 'description': 'Design jobs'},
        {'name': 'Education & Training', 'description': 'Education jobs'},
        {'name': 'Retail & Sales', 'description': 'Retail jobs'},
        {'name': 'Hospitality & Tourism', 'description': 'Hospitality jobs'},
        {'name': 'Legal Services', 'description': 'Legal jobs'},
    ]
    
    created = 0
    for cat in categories:
        _, cat_created = JobCategory.objects.get_or_create(
            name=cat['name'],
            defaults={'description': cat['description']}
        )
        if cat_created:
            created += 1
    print(f"✅ Created {created} job categories")

def create_10_jobs_per_company():
    """Create exactly 10 industry-appropriate jobs for each company"""
    
    # Industry-specific job templates
    job_templates = {
        'it': [
            ("Senior Software Engineer", "full_time", 1200000, 2000000),
            ("Frontend Developer (React)", "full_time", 900000, 1500000),
            ("Backend Developer (Python)", "full_time", 1000000, 1700000),
            ("DevOps Engineer", "full_time", 1100000, 1800000),
            ("Data Scientist", "full_time", 1300000, 2200000),
            ("QA Engineer", "full_time", 800000, 1300000),
            ("UI/UX Designer", "full_time", 700000, 1200000),
            ("Product Manager", "full_time", 1500000, 2500000),
            ("Cloud Architect", "full_time", 1400000, 2300000),
            ("Cybersecurity Analyst", "full_time", 1200000, 2000000),
        ],
        
        'healthcare': [
            ("Medical Doctor", "full_time", 1800000, 3000000),
            ("Staff Nurse", "full_time", 400000, 700000),
            ("Pharmacist", "full_time", 600000, 1000000),
            ("Medical Lab Technician", "full_time", 300000, 500000),
            ("Physiotherapist", "full_time", 500000, 900000),
            ("Hospital Administrator", "full_time", 800000, 1400000),
            ("Radiology Technician", "full_time", 350000, 600000),
            ("Dietitian/Nutritionist", "full_time", 400000, 700000),
            ("Surgeon", "full_time", 2500000, 4000000),
            ("Pediatrician", "full_time", 1600000, 2800000),
        ],
        
        'banking': [
            ("Branch Manager", "full_time", 1200000, 2000000),
            ("Financial Analyst", "full_time", 800000, 1400000),
            ("Relationship Manager", "full_time", 900000, 1600000),
            ("Loan Officer", "full_time", 600000, 1000000),
            ("Investment Banker", "full_time", 2000000, 3500000),
            ("Credit Analyst", "full_time", 700000, 1200000),
            ("Wealth Manager", "full_time", 1500000, 2500000),
            ("Compliance Officer", "full_time", 1000000, 1800000),
            ("Digital Banking Specialist", "full_time", 900000, 1500000),
            ("Risk Manager", "full_time", 1300000, 2200000),
        ],
        
        'manufacturing': [
            ("Production Manager", "full_time", 1000000, 1800000),
            ("Quality Control Engineer", "full_time", 600000, 1000000),
            ("Supply Chain Manager", "full_time", 900000, 1600000),
            ("Mechanical Engineer", "full_time", 700000, 1200000),
            ("Industrial Designer", "full_time", 600000, 1100000),
            ("Automation Engineer", "full_time", 800000, 1400000),
            ("Maintenance Engineer", "full_time", 550000, 950000),
            ("Safety Officer", "full_time", 400000, 700000),
            ("Procurement Manager", "full_time", 900000, 1600000),
            ("Operations Head", "full_time", 1500000, 2500000),
        ],
        
        'ecommerce': [
            ("E-commerce Manager", "full_time", 1000000, 1800000),
            ("Digital Marketing Manager", "full_time", 900000, 1600000),
            ("Supply Chain Analyst", "full_time", 700000, 1200000),
            ("Product Manager", "full_time", 1200000, 2000000),
            ("SEO Specialist", "full_time", 500000, 900000),
            ("Social Media Manager", "full_time", 400000, 700000),
            ("Logistics Manager", "full_time", 800000, 1400000),
            ("Category Manager", "full_time", 900000, 1600000),
            ("Marketplace Specialist", "full_time", 600000, 1100000),
            ("Data Analyst (E-commerce)", "full_time", 800000, 1400000),
        ],
        
        'education': [
            ("Mathematics Teacher", "full_time", 400000, 700000),
            ("Science Teacher", "full_time", 400000, 700000),
            ("English Teacher", "full_time", 400000, 700000),
            ("School Principal", "full_time", 1000000, 1800000),
            ("Academic Coordinator", "full_time", 600000, 1000000),
            ("Counsellor", "full_time", 500000, 900000),
            ("Special Education Teacher", "full_time", 450000, 800000),
            ("Curriculum Developer", "full_time", 600000, 1100000),
            ("Online Tutor", "part_time", 15000, 30000),
            ("Admissions Officer", "full_time", 400000, 700000),
        ],
        
        'food_delivery': [
            ("Delivery Operations Manager", "full_time", 800000, 1400000),
            ("Restaurant Partnerships Manager", "full_time", 900000, 1600000),
            ("Food Quality Analyst", "full_time", 500000, 900000),
            ("Customer Support Head", "full_time", 700000, 1200000),
            ("City Operations Manager", "full_time", 1000000, 1800000),
            ("Marketing Specialist", "full_time", 600000, 1100000),
            ("Data Analyst (Operations)", "full_time", 700000, 1300000),
            ("Business Development Executive", "full_time", 500000, 900000),
            ("Restaurant Onboarding Specialist", "full_time", 500000, 900000),
            ("Customer Experience Manager", "full_time", 700000, 1200000),
        ],
        
        'retail': [
            ("Store Manager", "full_time", 700000, 1200000),
            ("Assistant Store Manager", "full_time", 500000, 900000),
            ("Visual Merchandiser", "full_time", 400000, 700000),
            ("Inventory Manager", "full_time", 600000, 1000000),
            ("Buyer/Merchandiser", "full_time", 700000, 1200000),
            ("Retail Operations Manager", "full_time", 900000, 1600000),
            ("Department Supervisor", "full_time", 450000, 800000),
            ("Loss Prevention Officer", "full_time", 300000, 500000),
            ("Beauty Advisor", "full_time", 250000, 450000),
            ("Fashion Consultant", "full_time", 300000, 550000),
        ],
    }
    
    # Map industries to categories
    industry_to_category = {
        'it': 'Information Technology',
        'healthcare': 'Healthcare',
        'banking': 'Finance & Banking',
        'manufacturing': 'Engineering',
        'ecommerce': 'Business & Management',
        'education': 'Education & Training',
        'food_delivery': 'Business & Management',
        'retail': 'Retail & Sales',
    }
    
    print("\n🏢 CREATING 10 JOBS FOR EACH COMPANY:")
    print("=" * 50)
    
    total_jobs_created = 0
    companies = Company.objects.all()
    
    for company in companies:
        # Get industry from company
        industry = company.industry if company.industry else 'it'
        
        # Get job templates for this industry
        templates = job_templates.get(industry, job_templates['it'])
        
        # Get category for this industry
        category_name = industry_to_category.get(industry, 'Information Technology')
        category_obj, _ = JobCategory.objects.get_or_create(
            name=category_name,
            defaults={'description': f'{industry} related jobs'}
        )
        
        print(f"\n📋 {company.name} ({industry}):")
        
        # Create exactly 10 jobs
        for i in range(min(10, len(templates))):
            title, job_type, min_sal, max_sal = templates[i]
            
            job = Job.objects.create(
                company=company,
                category=category_obj,
                title=title,
                job_type=job_type,
                location=random.choice(["Bangalore", "Mumbai", "Delhi", "Hyderabad", "Chennai", "Pune", "Kolkata"]),
                description=f"Join {company.name} as a {title}. We offer competitive salary, great work environment, and growth opportunities.",
                requirements=f"• Relevant experience in {industry}\n• Strong communication skills\n• Team player\n• Problem-solving abilities\n• Willingness to learn",
                salary_min=min_sal,
                salary_max=max_sal,
                experience_level=random.choice(["Fresher", "1-3 years", "3-5 years", "5+ years"]),
                skills_required=f"{industry} skills, Communication, Teamwork, Problem Solving, Analytical Thinking",
                education_required=random.choice([
                    "Bachelor's degree in relevant field",
                    "Master's degree preferred",
                    "Diploma with relevant experience",
                    "Graduate in any discipline with certification"
                ]),
                is_active=True,
                is_remote=random.choice([True, False]),
                is_featured=(i < 3),  # First 3 jobs featured
                vacancy_count=random.randint(1, 5),
                application_deadline=timezone.now().date() + timedelta(days=random.randint(30, 90))
            )
            
            total_jobs_created += 1
            print(f"   {i+1:2d}. {title} (₹{min_sal:,} - ₹{max_sal:,})")
    
    return total_jobs_created

def create_analytics():
    """Create realistic analytics for all companies"""
    print("\n📊 CREATING ANALYTICS DATA...")
    
    for company in Company.objects.all():
        job_count = company.job_set.count()
        CompanyAnalytics.objects.create(
            company=company,
            total_job_views=random.randint(job_count * 50, job_count * 100),
            total_applications=random.randint(job_count * 5, job_count * 15),
            total_hires=random.randint(job_count * 1, job_count * 3),
            avg_time_to_hire=random.uniform(15, 30),
            application_conversion=random.uniform(5, 20),
        )
    print(f"✅ Created analytics for {Company.objects.count()} companies")

def main():
    print("=" * 60)
    print("JOBORA - DATA POPULATION WITH UNIQUE PASSWORDS")
    print("=" * 60)
    
    # Step 1: Create/Update companies with UNIQUE passwords
    if not create_or_update_company_users():
        print("❌ Failed to create company users")
        return
    
    # Step 2: Clear existing jobs/analytics
    clear_existing_data()
    
    # Step 3: Create categories
    create_job_categories()
    
    # Step 4: Create 10 jobs per company
    total_jobs = create_10_jobs_per_company()
    
    # Step 5: Create analytics
    create_analytics()
    
    # Final report
    print("\n" + "=" * 60)
    print("DATA POPULATION COMPLETE!")
    print("=" * 60)
    
    # Display sample credentials
    print(f"\n🔑 SAMPLE CREDENTIALS (UNIQUE PASSWORDS):")
    print("-" * 50)
    
    companies = Company.objects.all()[:5]
    for company in companies:
        username = company.user.username
        print(f"🏢 {company.name}")
        print(f"   Username: {username}")
        print(f"   Password: Check 'company_credentials_SECURE.txt' file")
        print()
    
    print(f"📊 FINAL SUMMARY:")
    print(f"   • Total Companies: {Company.objects.count()}")
    print(f"   • Total Jobs Created: {total_jobs}")
    print(f"   • Jobs per Company: 10")
    print(f"   • Each company has a UNIQUE secure password")
    
    print(f"\n📁 Important Files:")
    print(f"   • company_credentials_SECURE.txt - All login details")
    print(f"   • DO NOT SHARE or commit to Git!")
    
    print(f"\n🎯 READY FOR PROFESSIONAL DEMO! 🚀")

if __name__ == '__main__':
    main()