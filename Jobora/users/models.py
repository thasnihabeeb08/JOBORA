from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Company(models.Model):
    INDUSTRY_CHOICES = [
        ('it', 'Information Technology'),
        ('healthcare', 'Healthcare'),
        ('finance', 'Finance & Banking'),
        ('education', 'Education'),
        ('retail', 'Retail'),
        ('manufacturing', 'Manufacturing'),
        ('real_estate', 'Real Estate'),
        ('hospitality', 'Hospitality & Tourism'),
        ('legal', 'Legal Services'),
        ('engineering', 'Engineering'),
        ('design', 'Design & Creative'),
        ('marketing', 'Marketing & Advertising'),
        ('consulting', 'Consulting'),
        ('non_profit', 'Non-Profit'),
        ('other', 'Other'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company_profile')
    name = models.CharField(max_length=200, unique=True)
    contact_person = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    location = models.CharField(max_length=100)
    industry = models.CharField(max_length=50, choices=INDUSTRY_CHOICES)
    email = models.EmailField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class UserProfile(models.Model):
    USER_TYPES = (
        ('student', 'Student'),
        ('fresher', 'Fresher (0-2 years)'),
        ('experienced', 'Experienced Professional (2+ years)'),
        ('part_time', 'Part-time Worker'),
        ('freelancer', 'Freelancer'),
    )
    
    EDUCATION_LEVELS = (
        ('high_school', 'High School'),
        ('diploma', 'Diploma'),
        ('bachelors', "Bachelor's Degree"),
        ('masters', "Master's Degree"),
        ('phd', 'PhD'),
        ('other', 'Other'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    headline = models.CharField(max_length=200, blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='fresher')
    highest_education = models.CharField(max_length=20, choices=EDUCATION_LEVELS, blank=True, null=True)
    field_of_study = models.CharField(max_length=200, blank=True, null=True)
    institution = models.CharField(max_length=200, blank=True, null=True)
    graduation_year = models.IntegerField(
        blank=True, 
        null=True,
        validators=[MinValueValidator(1950), MaxValueValidator(timezone.now().year + 5)]
    )
    years_experience = models.PositiveIntegerField(default=0)
    current_role = models.CharField(max_length=200, blank=True, null=True)
    current_company = models.CharField(max_length=200, blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    preferred_job_types = models.CharField(max_length=200, blank=True, null=True)
    preferred_locations = models.TextField(blank=True, null=True)
    
    # ========== FIXED: Changed from DecimalField to PositiveIntegerField ==========
    salary_expectation = models.PositiveIntegerField(
        blank=True, 
        null=True,
        help_text="Expected annual salary in whole rupees (e.g., 500000 for ₹5 Lakhs)"
    )
    
    portfolio_link = models.URLField(blank=True, null=True)
    github_profile = models.URLField(blank=True, null=True)
    linkedin_profile = models.URLField(blank=True, null=True)
    availability_status = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immediately Available'),
            ('2_weeks', 'Available in 2 Weeks'),
            ('1_month', 'Available in 1 Month'),
            ('notice_period', 'Serving Notice Period'),
            ('not_available', 'Not Available'),
        ],
        default='immediate',
        blank=True
    )
    notice_period_days = models.IntegerField(default=0, blank=True)
    expected_joining_date = models.DateField(blank=True, null=True)
    work_preference = models.CharField(
        max_length=20,
        choices=[
            ('office', 'Office Only'),
            ('hybrid', 'Hybrid'),
            ('remote', 'Remote Only'),
            ('flexible', 'Flexible'),
        ],
        default='flexible',
        blank=True
    )
    willing_to_relocate = models.BooleanField(default=True)
    willing_to_travel = models.BooleanField(default=False)
    travel_percentage = models.IntegerField(default=0, blank=True)
    is_active_seeker = models.BooleanField(default=True)
    job_search_intensity = models.CharField(
        max_length=20,
        choices=[
            ('casual', 'Casual Search'),
            ('active', 'Active Search'),
            ('urgent', 'Urgent - Need Job ASAP'),
        ],
        default='active',
        blank=True
    )
    certifications = models.TextField(blank=True, null=True)
    awards = models.TextField(blank=True, null=True)
    preferred_company_size = models.CharField(
        max_length=20,
        choices=[
            ('startup', 'Startup (1-50 employees)'),
            ('small', 'Small (51-200 employees)'),
            ('medium', 'Medium (201-1000 employees)'),
            ('large', 'Large (1000+ employees)'),
            ('any', 'Any Size'),
        ],
        default='any',
        blank=True
    )
    ai_match_preferences = models.JSONField(default=dict, blank=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_profile_complete = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_applications = models.PositiveIntegerField(default=0)
    applications_shortlisted = models.PositiveIntegerField(default=0)
    applications_selected = models.PositiveIntegerField(default=0)
    profile_views = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    @property
    def full_name(self):
        try:
            name = self.user.get_full_name()
            if name:
                return name
        except:
            pass
        return self.user.username
    
    @property
    def email(self):
        try:
            return self.user.email
        except:
            return ""
    
    @property
    def completion_percentage(self):
        try:
            required_fields = [
                self.phone, self.location, self.headline, 
                self.summary, self.skills, self.resume
            ]
            completed = sum(1 for field in required_fields if field and str(field).strip())
            percentage = int((completed / len(required_fields)) * 100) if required_fields else 0
            return min(percentage, 100)
        except:
            return 0
    
    @property
    def skills_list(self):
        try:
            if self.skills:
                return [skill.strip() for skill in self.skills.split(',') if skill.strip()]
        except:
            pass
        return []
    
    class Meta:
        verbose_name = "Job Seeker Profile"
        verbose_name_plural = "Job Seeker Profiles"

class SavedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey('jobs.Job', on_delete=models.CASCADE, related_name='saved_by_users')
    saved_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'job']
        ordering = ['-saved_at']
    
    def __str__(self):
        return f"{self.user.username} saved {self.job.title}"

class SavedSearch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_searches')
    name = models.CharField(max_length=100)
    search_params = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']

class JobAlert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_alerts')
    name = models.CharField(max_length=100)
    search_params = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']