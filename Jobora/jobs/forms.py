# jobs/forms.py - COMPLETE FIXED VERSION
from django import forms
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, URLValidator, EmailValidator
from django.core.exceptions import ValidationError
import re
from .models import Job, Application, Interview, JobCategory, Message
from users.models import Company
from django.utils import timezone
from datetime import date, datetime, timedelta

# ==================== VALIDATORS ====================

# Simplified Indian mobile number validator
indian_mobile_validator = RegexValidator(
    regex=r'^[6-9]\d{9}$',
    message='Enter a valid mobile number',
    code='invalid_mobile'
)

# Company name validator
company_name_validator = RegexValidator(
    regex=r'^[a-zA-Z0-9\s&.\'-]+$',
    message='Enter a valid company name',
    code='invalid_company_name'
)

# Contact person validator
contact_person_validator = RegexValidator(
    regex=r'^[a-zA-Z\s.-]+$',
    message='Enter a valid name',
    code='invalid_name'
)

# Email uniqueness validator
def validate_unique_email(email, exclude_user=None):
    if User.objects.filter(email=email).exclude(pk=exclude_user.pk if exclude_user else None).exists():
        raise ValidationError('This email is already registered')

# ==================== FORMS ====================

class CompanyProfileForm(forms.ModelForm):
    # Email field (from User model)
    email = forms.EmailField(
        required=True,
        validators=[EmailValidator(message='Enter a valid email address')],
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'company@example.com',
            'id': 'id_email'
        }),
        label="Email Address *",
        help_text="Your primary contact email"
    )
    
    # Company name
    company_name = forms.CharField(
        max_length=200,
        required=True,
        validators=[company_name_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Tech Innovations Pvt Ltd',
            'id': 'id_company_name'
        }),
        label="Company Name *",
        help_text="Official registered name of your company"
    )
    
    # Phone
    phone = forms.CharField(
        max_length=15,
        required=True,
        validators=[indian_mobile_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '9876543210',
            'id': 'id_mobile'
        }),
        label="Mobile Number *",
        help_text="10-digit Indian mobile number"
    )
    
    # Contact person
    contact_person = forms.CharField(
        max_length=100,
        required=True,
        validators=[contact_person_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'John Doe',
            'id': 'id_contact_person'
        }),
        label="Contact Person *",
        help_text="Primary contact person for recruitment"
    )
    
    # Location
    location = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Bangalore, Karnataka',
            'id': 'id_location'
        }),
        label="Location *",
        help_text="City, State where your company operates"
    )
    
    # Industry selection
    industry = forms.ChoiceField(
        choices=Company.INDUSTRY_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_industry'
        }),
        label="Industry *",
        help_text="Select your primary business industry"
    )
    
    # Description
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Describe your company culture, mission, values...',
            'id': 'id_description',
            'maxlength': '2000'
        }),
        label="Company Description",
        help_text="Max 2000 characters"
    )
    
    # Logo
    logo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'accept': 'image/*',
            'id': 'id_logo'
        }),
        label="Company Logo",
        help_text="Recommended: 300×300px, JPG/PNG format"
    )
    
    class Meta:
        model = Company
        fields = [
            'company_name', 'contact_person', 'phone', 
            'location', 'industry', 'description', 'logo'
        ]
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Initialize values
        if self.instance and self.instance.pk:
            self.fields['company_name'].initial = self.instance.name
            if self.instance.user:
                self.fields['email'].initial = self.instance.user.email
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        email = email.strip().lower()
        
        # Check email uniqueness
        if self.instance and self.instance.user:
            validate_unique_email(email, self.instance.user)
        else:
            validate_unique_email(email)
        
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove any non-digit characters
            phone = re.sub(r'\D', '', phone)
            if len(phone) != 10:
                raise ValidationError("Enter a valid mobile number")
            if not phone.startswith(('6', '7', '8', '9')):
                raise ValidationError("Enter a valid mobile number")
        return phone
    
    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if logo:
            # Check file size (max 2MB)
            max_size = 2 * 1024 * 1024  # 2MB
            if logo.size > max_size:
                raise ValidationError("File size must be less than 2MB")
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'image/gif']
            if logo.content_type not in allowed_types:
                raise ValidationError("Only JPG, PNG, and GIF images are allowed")
        
        return logo
    
    def clean_description(self):
        description = self.cleaned_data.get('description', '')
        if len(description) > 2000:
            raise ValidationError("Description cannot exceed 2000 characters")
        return description
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Ensure required fields are not empty
        required_fields = ['company_name', 'email', 'contact_person', 'phone', 'location', 'industry']
        for field in required_fields:
            if not cleaned_data.get(field):
                self.add_error(field, "This field is required")
        
        return cleaned_data
    
    def save(self, commit=True):
        company = super().save(commit=False)
        
        # Map company_name to name field
        company.name = self.cleaned_data.get('company_name', '')
        
        # Update User email if changed
        email = self.cleaned_data.get('email')
        if email and company.user and company.user.email != email:
            company.user.email = email
            if commit:
                company.user.save()
        
        if commit:
            company.save()
        
        return company

# ==================== JobPostForm ====================

class JobPostForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=JobCategory.objects.all().order_by('name'),
        empty_label="Select Job Category",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Job Category *"
    )
    
    class Meta:
        model = Job
        fields = [
            'title', 'description', 'requirements', 'job_type', 'category',
            'experience_level', 'salary_min', 'salary_max', 'location', 
            'is_remote', 'skills_required', 'education_required',
            'application_deadline', 'vacancy_count'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Senior Python Developer',
                'id': 'id_title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Detailed job description...',
                'id': 'id_description'
            }),
            'requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Requirements and qualifications...',
                'id': 'id_requirements'
            }),
            'job_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_job_type'
            }),
            'experience_level': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_experience_level'
            }),
            'salary_min': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Minimum salary (₹)',
                'id': 'id_salary_min',
                'min': '0'
            }),
            'salary_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Maximum salary (₹)',
                'id': 'id_salary_max',
                'min': '0'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Bangalore, Karnataka',
                'id': 'id_location'
            }),
            'is_remote': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_is_remote'
            }),
            'skills_required': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Python, Django, React, PostgreSQL (comma separated)',
                'id': 'id_skills_required'
            }),
            'education_required': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Education requirements...',
                'id': 'id_education_required'
            }),
            'application_deadline': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': date.today().isoformat(),
                'id': 'id_application_deadline'
            }),
            'vacancy_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'id': 'id_vacancy_count'
            }),
        }
        labels = {
            'salary_min': 'Minimum Salary (₹) *',
            'salary_max': 'Maximum Salary (₹)',
            'is_remote': 'Remote Position',
            'vacancy_count': 'Number of Vacancies *',
        }
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        today = date.today()
        self.fields['application_deadline'].widget.attrs['min'] = today.isoformat()
        
        if self.company:
            self.instance.company = self.company
    
    def clean(self):
        cleaned_data = super().clean()
        
        salary_min = cleaned_data.get('salary_min')
        salary_max = cleaned_data.get('salary_max')
        
        if salary_min is not None and salary_min < 0:
            self.add_error('salary_min', 'Enter a valid salary')
        
        if salary_max is not None and salary_max < 0:
            self.add_error('salary_max', 'Enter a valid salary')
        
        if salary_min and salary_max and salary_min > salary_max:
            self.add_error('salary_max', 'Maximum salary must be greater than minimum salary')
        
        deadline = cleaned_data.get('application_deadline')
        if deadline and deadline < date.today():
            self.add_error('application_deadline', 'Select a future date')
        
        vacancy_count = cleaned_data.get('vacancy_count')
        if vacancy_count is not None and vacancy_count < 1:
            self.add_error('vacancy_count', 'Enter a valid number')
        
        required_fields = ['title', 'description', 'requirements', 'job_type', 
                          'category', 'experience_level', 'location', 'skills_required']
        for field in required_fields:
            if not cleaned_data.get(field):
                self.add_error(field, "This field is required")
        
        return cleaned_data
    
    def save(self, commit=True):
        job = super().save(commit=False)
        
        if not job.company and self.company:
            job.company = self.company
        
        if commit:
            job.save()
        
        return job

# ==================== ApplicationFilterForm - FIXED VERSION ====================

class ApplicationFilterForm(forms.Form):
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('applied', 'Applied'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
        ('selected', 'Selected'),
        ('interview', 'Interview Scheduled'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_status'
        })
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'id': 'id_date_from'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'id': 'id_date_to'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            self.add_error('date_to', 'End date must be after start date')
        
        # Ensure date range is reasonable (max 1 year)
        if date_from and date_to:
            if (date_to - date_from).days > 365:
                self.add_error('date_to', 'Date range cannot exceed 1 year')
        
        return cleaned_data
    
    def filter_queryset(self, queryset):
        """Helper method to apply filters to queryset - FIXED DATE FILTERING"""
        data = self.cleaned_data
        
        # Apply status filter
        status = data.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Apply date from filter (applications on or after this date)
        date_from = data.get('date_from')
        if date_from:
            queryset = queryset.filter(applied_on__date__gte=date_from)
        
        # Apply date to filter (applications on or before this date)
        # FIXED: Add +1 day to include the end date properly
        date_to = data.get('date_to')
        if date_to:
            date_to_inclusive = date_to + timedelta(days=1)
            queryset = queryset.filter(applied_on__date__lt=date_to_inclusive)
        
        return queryset

# ==================== InterviewScheduleForm ====================

class InterviewScheduleForm(forms.ModelForm):
    class Meta:
        model = Interview
        fields = ['scheduled_date', 'interview_type', 'platform', 
                  'meeting_link', 'meeting_id', 'passcode', 'interviewer']
        widgets = {
            'scheduled_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
                'id': 'id_scheduled_date'
            }),
            'interview_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_interview_type'
            }),
            'platform': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Google Meet, Zoom, Microsoft Teams',
                'id': 'id_platform'
            }),
            'meeting_link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://meet.google.com/xxx-xxxx-xxx',
                'id': 'id_meeting_link'
            }),
            'meeting_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Meeting ID',
                'id': 'id_meeting_id'
            }),
            'passcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Passcode (if any)',
                'id': 'id_passcode'
            }),
            'interviewer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Interviewer name',
                'id': 'id_interviewer'
            }),
        }
    
    def clean_scheduled_date(self):
        scheduled_date = self.cleaned_data.get('scheduled_date')
        if scheduled_date and scheduled_date <= timezone.now():
            raise ValidationError("Select a future date/time")
        
        max_date = timezone.now() + timedelta(days=180)
        if scheduled_date and scheduled_date > max_date:
            raise ValidationError("Select a date within 6 months")
        
        return scheduled_date

# ==================== MessageForm ====================

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['subject', 'content']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Subject',
                'id': 'id_subject',
                'maxlength': '200'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Your message...',
                'id': 'id_content',
                'maxlength': '5000'
            }),
        }
    
    def clean_subject(self):
        subject = self.cleaned_data.get('subject', '')
        if len(subject.strip()) == 0:
            raise ValidationError("Enter a subject")
        if len(subject) > 200:
            raise ValidationError("Subject is too long")
        return subject.strip()
    
    def clean_content(self):
        content = self.cleaned_data.get('content', '')
        if len(content.strip()) == 0:
            raise ValidationError("Enter message content")
        if len(content) > 5000:
            raise ValidationError("Message is too long")
        return content.strip()