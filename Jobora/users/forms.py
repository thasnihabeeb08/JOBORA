from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox
import re
from datetime import date

from .models import UserProfile

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

JOB_TYPES = [
    ('full_time', 'Full-time'),
    ('part_time', 'Part-time'),
    ('internship', 'Internship'),
    ('freelance', 'Freelance/Contract'),
]

class CompanyRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'company@example.com'
        }),
        label="Company Email *"
    )
    
    company_name = forms.CharField(
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Company Name'
        }),
        label="Company Name *"
    )
    
    phone = forms.CharField(
        required=True,
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '9876543210'
        }),
        label="Phone Number *"
    )
    
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(attrs={
            'data-theme': 'light',
            'data-size': 'normal',
        })
    )
    
    class Meta:
        model = User
        fields = ['email', 'company_name', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('username', None)
        
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    
    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email is already registered')
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        phone = re.sub(r'\D', '', phone)
        
        if len(phone) != 10:
            raise forms.ValidationError('Phone number must be exactly 10 digits')
        
        if not phone.startswith(('6', '7', '8', '9')):
            raise forms.ValidationError('Indian mobile number must start with 6, 7, 8, or 9')
        
        return phone
    
    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data['email']
        user.email = email
        user.username = email
        
        if commit:
            user.save()
        
        return user

class JobSeekerRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com'
        }),
        label="Email Address *"
    )
    
    first_name = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'John'
        }),
        label="First Name *"
    )
    
    last_name = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Doe'
        }),
        label="Last Name *"
    )
    
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label="Date of Birth *"
    )
    
    phone = forms.CharField(
        required=True,
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '9876543210'
        }),
        label="Phone Number *"
    )
    
    location = forms.CharField(
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City, State'
        }),
        label="Location *"
    )
    
    user_type = forms.ChoiceField(
        required=True,
        choices=USER_TYPES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label="Professional Category *"
    )
    
    highest_education = forms.ChoiceField(
        required=True,
        choices=EDUCATION_LEVELS,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label="Highest Education *"
    )
    
    field_of_study = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Computer Science'
        }),
        label="Field of Study"
    )
    
    institution = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'University/College'
        }),
        label="Institution"
    )
    
    years_experience = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=50,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0'
        }),
        label="Years of Experience"
    )
    
    current_role = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Software Engineer'
        }),
        label="Current Role"
    )
    
    skills = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Python, Django, JavaScript, Communication...'
        }),
        label="Skills *"
    )
    
    preferred_job_types = forms.MultipleChoiceField(
        required=True,
        choices=JOB_TYPES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label="Job Type Preferences *"
    )
    
    preferred_locations = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Bangalore, Mumbai, Remote...'
        }),
        label="Preferred Locations"
    )
    
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(attrs={
            'data-theme': 'light',
            'data-size': 'normal',
        })
    )
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('username', None)
        
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
        
        today = date.today()
        min_date = date(today.year - 100, 1, 1)
        max_date = date(today.year - 18, today.month, today.day)
        self.fields['date_of_birth'].widget.attrs['min'] = min_date.isoformat()
        self.fields['date_of_birth'].widget.attrs['max'] = max_date.isoformat()
    
    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email is already registered')
        return email
    
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                raise forms.ValidationError('You must be at least 18 years old to register')
            if age > 100:
                raise forms.ValidationError('Please enter a valid date of birth')
        return dob
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        phone = re.sub(r'\D', '', phone)
        
        if len(phone) != 10:
            raise forms.ValidationError('Phone number must be exactly 10 digits')
        
        if not phone.startswith(('6', '7', '8', '9')):
            raise forms.ValidationError('Indian mobile number must start with 6, 7, 8, or 9')
        
        return phone
    
    def clean_skills(self):
        skills = self.cleaned_data.get('skills', '').strip()
        if not skills:
            raise forms.ValidationError('Please enter your skills')
        
        skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
        if len(skills_list) == 0:
            raise forms.ValidationError('Please enter at least one skill')
        
        return skills
    
    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data['email']
        user.email = email
        user.username = email
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            
            profile = UserProfile.objects.create(
                user=user,
                phone=self.cleaned_data.get('phone'),
                location=self.cleaned_data.get('location'),
                date_of_birth=self.cleaned_data.get('date_of_birth'),
                user_type=self.cleaned_data.get('user_type'),
                highest_education=self.cleaned_data.get('highest_education'),
                field_of_study=self.cleaned_data.get('field_of_study', ''),
                institution=self.cleaned_data.get('institution', ''),
                years_experience=self.cleaned_data.get('years_experience', 0),
                current_role=self.cleaned_data.get('current_role', ''),
                skills=self.cleaned_data.get('skills'),
                preferred_job_types=','.join(self.cleaned_data.get('preferred_job_types', [])),
                preferred_locations=self.cleaned_data.get('preferred_locations', ''),
                is_profile_complete=True
            )
        
        return user

class ApplicationForm(forms.Form):
    cover_letter = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Write your cover letter here...'
        }),
        label="Cover Letter *"
    )
    
    expected_salary = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '800000',
            'min': '0',
            'step': '10000'
        }),
        label="Expected Salary (₹ per annum)",
        help_text="Annual salary expectation. Leave blank if negotiable."
    )
    
    resume = forms.FileField(
        required=False,
        validators=[FileExtensionValidator(['pdf', 'doc', 'docx'])],
        widget=forms.FileInput(attrs={
            'class': 'form-control'
        }),
        label="Resume (Optional)"
    )
    
    def clean_expected_salary(self):
        salary = self.cleaned_data.get('expected_salary')
        if salary is not None:
            if salary < 0:
                raise forms.ValidationError('Salary cannot be negative')
            if salary > 50000000:
                raise forms.ValidationError('Please enter a realistic salary expectation')
        return salary

class JobSearchForm(forms.Form):
    keyword = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Job title, skills, or company'
        }),
        label="Keyword"
    )
    
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City, state, or remote'
        }),
        label="Location"
    )
    
    job_type = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Any Type'),
            ('full_time', 'Full Time'),
            ('part_time', 'Part Time'),
            ('internship', 'Internship'),
            ('freelance', 'Freelance'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label="Job Type"
    )
    
    experience_level = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Any Level'),
            ('entry', 'Entry Level'),
            ('mid', 'Mid Level'),
            ('senior', 'Senior Level'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label="Experience Level"
    )
    
    salary_min = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min Salary (₹)'
        }),
        label="Minimum Salary"
    )
    
    salary_max = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max Salary (₹)'
        }),
        label="Maximum Salary"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        salary_min = cleaned_data.get('salary_min')
        salary_max = cleaned_data.get('salary_max')
        
        if salary_min and salary_max:
            if salary_min > salary_max:
                raise forms.ValidationError('Minimum salary cannot be greater than maximum salary')
        
        return cleaned_data

class UserProfileForm(forms.ModelForm):
    # Add preferred_job_types field to the form
    preferred_job_types = forms.MultipleChoiceField(
        required=False,
        choices=JOB_TYPES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label="Preferred Job Types"
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'phone', 'date_of_birth', 'location', 'headline', 'summary',
            'user_type', 'highest_education', 'field_of_study', 'institution',
            'graduation_year', 'years_experience', 'current_role', 'current_company',
            'skills', 'certifications', 'awards', 'preferred_locations',
            'salary_expectation', 'profile_picture', 'resume'
        ]
        
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'headline': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Senior Python Developer'}),
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Write a brief summary of your professional background...'}),
            'skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Python, Django, JavaScript, Communication, Teamwork...'}),
            'certifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'AWS Certified, Google Analytics...'}),
            'awards': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Employee of the Month, Hackathon Winner...'}),
            'preferred_locations': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Bangalore, Mumbai, Delhi, Remote...'}),
            'salary_expectation': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '800000', 'min': '0', 'step': '10000'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initialize preferred_job_types with current value
        if self.instance and self.instance.preferred_job_types:
            initial_job_types = [t.strip() for t in self.instance.preferred_job_types.split(',') if t.strip()]
            self.fields['preferred_job_types'].initial = initial_job_types
        
        # Set required fields
        required_fields = ['phone', 'date_of_birth', 'location', 'user_type', 'highest_education', 'skills']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
        
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                if isinstance(field.widget, forms.CheckboxSelectMultiple):
                    field.widget.attrs['class'] = 'form-check-input'
                elif isinstance(field.widget, forms.Textarea):
                    field.widget.attrs['class'] = 'form-control'
                elif isinstance(field.widget, forms.Select):
                    field.widget.attrs['class'] = 'form-control'
                else:
                    field.widget.attrs['class'] = 'form-control'
    
    def save(self, commit=True):
        # Save preferred_job_types
        profile = super().save(commit=False)
        preferred_job_types = self.cleaned_data.get('preferred_job_types', [])
        profile.preferred_job_types = ','.join(preferred_job_types) if preferred_job_types else ''
        
        if commit:
            profile.save()
        
        return profile
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        phone = re.sub(r'\D', '', phone)
        
        if phone and len(phone) != 10:
            raise forms.ValidationError('Phone number must be exactly 10 digits')
        
        if phone and not phone.startswith(('6', '7', '8', '9')):
            raise forms.ValidationError('Indian mobile number must start with 6, 7, 8, or 9')
        
        return phone
    
    def clean_skills(self):
        skills = self.cleaned_data.get('skills', '').strip()
        if not skills:
            raise forms.ValidationError('Please enter your skills')
        
        skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
        if len(skills_list) < 3:
            raise forms.ValidationError('Please enter at least 3 skills separated by commas')
        
        return skills
    
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                raise forms.ValidationError('You must be at least 18 years old')
            if age > 100:
                raise forms.ValidationError('Please enter a valid date of birth')
        return dob