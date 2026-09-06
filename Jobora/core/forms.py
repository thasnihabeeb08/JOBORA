from django import forms
from .models import SuccessStory
from .models import Feedback

class SuccessStoryForm(forms.ModelForm):
    consent = forms.BooleanField(
        required=True,
        error_messages={'required': 'You must agree to share your story'}
    )
    
    class Meta:
        model = SuccessStory
        fields = ['full_name', 'current_role', 'email', 'story_content', 'consent']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'placeholder': 'Enter your full name',
                'class': 'form-control'
            }),
            'current_role': forms.TextInput(attrs={
                'placeholder': 'e.g., Software Developer at Company', 
                'class': 'form-control'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Enter your email',
                'class': 'form-control'
            }),
            'story_content': forms.Textarea(attrs={
                'placeholder': 'Tell us about your journey...',
                'class': 'form-control',
                'rows': 5
            }),
        }
    
    def clean_full_name(self):
        name = self.cleaned_data['full_name'].strip()
        if len(name) < 3:
            raise forms.ValidationError('Name must be at least 3 characters long')
        if len(name) > 30:
            raise forms.ValidationError('Name cannot exceed 30 characters')
        # Allow letters, spaces, and common punctuation
        if not all(c.isalpha() or c.isspace() or c in ".-'" for c in name):
            raise forms.ValidationError('Name can only contain letters, spaces, and common punctuation')
        return name
    
    def clean_current_role(self):
        role = self.cleaned_data['current_role'].strip()
        if len(role) < 3:
            raise forms.ValidationError('Role must be at least 3 characters long')
        if len(role) > 50:
            raise forms.ValidationError('Role cannot exceed 50 characters')
        return role
    
    def clean_story_content(self):
        content = self.cleaned_data['story_content'].strip()
        if len(content) < 100:
            raise forms.ValidationError('Story must be at least 100 characters long')
        if len(content) > 2000:
            raise forms.ValidationError('Story cannot exceed 2000 characters')
        return content

        
class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['name', 'email', 'subject', 'message', 'rating']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter subject'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your feedback...',
                'rows': 5
            }),
            'rating': forms.Select(attrs={
                'class': 'form-control'
            }),
        }