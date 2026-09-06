from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta
from users.models import Company

class JobCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Job Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Job(models.Model):
    JOB_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('internship', 'Internship'),
        ('freelance', 'Freelance'),
    ]
    
    EXPERIENCE_LEVEL_CHOICES = [
        ('fresher', 'Fresher (0-1 years)'),
        ('junior', 'Junior (1-3 years)'),
        ('mid', 'Mid Level (3-6 years)'),
        ('senior', 'Senior (6-10 years)'),
        ('executive', 'Executive (10+ years)'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField()
    
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
    category = models.ForeignKey(JobCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs')
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES, default='fresher')
    
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    salary_currency = models.CharField(max_length=3, default='INR')
    
    location = models.CharField(max_length=100)
    is_remote = models.BooleanField(default=False)
    
    skills_required = models.TextField(help_text="Comma separated skills")
    education_required = models.TextField(blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    
    application_deadline = models.DateField()
    posted_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    vacancy_count = models.PositiveIntegerField(default=1)
    views_count = models.PositiveIntegerField(default=0)
    
    # ===== NEW PROPERTY ADDED HERE =====
    @property
    def skills_required_list(self):
        """Return skills as a list"""
        if not self.skills_required:
            return []
        # Split by comma and strip whitespace
        return [skill.strip() for skill in self.skills_required.split(',') if skill.strip()]
    
    class Meta:
        ordering = ['-posted_on']
    
    def __str__(self):
        return f"{self.title} - {self.company.name}"
    
    def is_expired(self):
        return timezone.now().date() > self.application_deadline

class Application(models.Model):
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
        ('selected', 'Selected'),
        ('interview', 'Interview Scheduled'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    
    cover_letter = models.TextField(blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    expected_salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    applied_on = models.DateTimeField(auto_now_add=True)
    shortlisted_on = models.DateTimeField(null=True, blank=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    # AI Matching Fields
    match_percentage = models.IntegerField(default=0, null=True, blank=True)
    rule_score = models.FloatField(default=0.0, null=True, blank=True)
    ai_score = models.FloatField(default=0.0, null=True, blank=True)
    
    class Meta:
        unique_together = ['job', 'candidate']
        ordering = ['-applied_on']
        indexes = [
            models.Index(fields=['match_percentage']),
        ]
    
    def __str__(self):
        return f"{self.candidate.username} - {self.job.title}"

class Interview(models.Model):
    INTERVIEW_TYPE_CHOICES = [
        ('virtual', 'Virtual (Video Call)'),
        ('phone', 'Phone Interview'),
        ('in_person', 'In-Person Interview'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
    ]
    
    application = models.ForeignKey(
        Application, 
        on_delete=models.CASCADE, 
        related_name='interviews'
    )
    
    scheduled_date = models.DateTimeField()
    interview_type = models.CharField(max_length=20, choices=INTERVIEW_TYPE_CHOICES, default='virtual')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    platform = models.CharField(max_length=100, blank=True, null=True)
    meeting_link = models.URLField(blank=True, null=True)
    meeting_id = models.CharField(max_length=100, blank=True, null=True)
    passcode = models.CharField(max_length=100, blank=True, null=True)
    
    location = models.TextField(blank=True, null=True, help_text="Address for in-person interviews")
    
    interviewer = models.CharField(max_length=200, default='Hiring Manager')
    duration_minutes = models.IntegerField(default=60, validators=[MinValueValidator(15), MaxValueValidator(480)])
    notes = models.TextField(blank=True, null=True)
    
    feedback = models.TextField(blank=True, null=True)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    
    cancellation_reason = models.TextField(blank=True, null=True)
    cancelled_by = models.CharField(max_length=20, blank=True, null=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_interviews'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_date']
        indexes = [
            models.Index(fields=['application', '-scheduled_date']),
            models.Index(fields=['status', 'scheduled_date']),
        ]
    
    def __str__(self):
        return f"Interview for {self.application.job.title} - {self.scheduled_date.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def is_upcoming(self):
        return self.scheduled_date > timezone.now() and self.status == 'scheduled'
    
    @property
    def is_today(self):
        return self.scheduled_date.date() == timezone.now().date()
    
    @property
    def can_cancel(self):
        if self.status != 'scheduled':
            return False
        time_until = self.scheduled_date - timezone.now()
        return time_until > timedelta(hours=2)

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    application = models.ForeignKey(Application, on_delete=models.CASCADE, null=True, blank=True, related_name='messages')
    
    subject = models.CharField(max_length=200)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.sender.username} to {self.recipient.username}: {self.subject[:50]}"

class CompanyAnalytics(models.Model):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='analytics')
    
    total_job_views = models.PositiveIntegerField(default=0)
    total_applications = models.PositiveIntegerField(default=0)
    total_hires = models.PositiveIntegerField(default=0)
    total_interviews_scheduled = models.PositiveIntegerField(default=0)
    
    avg_time_to_hire = models.FloatField(default=0)
    application_conversion = models.FloatField(default=0)
    
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Analytics for {self.company.name}"