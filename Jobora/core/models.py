from django.db import models
from django.conf import settings  # ADD THIS IMPORT
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, MaxLengthValidator

class BlogPost(models.Model):
    CATEGORY_CHOICES = [
        ('Career Growth', 'Career Growth'),
        ('Interview Tips', 'Interview Tips'),
        ('Resume Writing', 'Resume Writing'),
        ('Salary Guide', 'Salary Guide'),
        ('Networking', 'Networking'),
        ('Work Life Balance', 'Work Life Balance'),
    ]
    
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    content = models.TextField()
    image_url = models.URLField()
    date_posted = models.DateField(auto_now_add=True)
    excerpt = models.TextField()
    is_published = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-date_posted']

class SuccessStory(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Published'),
        ('rejected', 'Rejected'),
    ]
    
    full_name = models.CharField(
        max_length=100,
        validators=[
            MinLengthValidator(3, message='Name must be at least 3 characters long'),
            MaxLengthValidator(30, message='Name cannot exceed 30 characters')
        ]
    )
    current_role = models.CharField(
        max_length=100,
        validators=[
            MinLengthValidator(3, message='Role must be at least 3 characters long'),
            MaxLengthValidator(50, message='Role cannot exceed 50 characters')
        ]
    )
    email = models.EmailField()
    story_content = models.TextField(
        validators=[
            MinLengthValidator(100, message='Story must be at least 100 characters long'),
            MaxLengthValidator(2000, message='Story cannot exceed 2000 characters')
        ]
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    consent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # FIX THIS LINE: Change User to settings.AUTH_USER_MODEL
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # CHANGED FROM User
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_stories'
    )
    
    class Meta:
        verbose_name_plural = "Success Stories"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name} - {self.current_role}"
    
    def get_initials(self):
        names = self.full_name.split()
        if len(names) >= 2:
            return (names[0][0] + names[-1][0]).upper()
        return self.full_name[:2].upper() if len(self.full_name) >= 2 else self.full_name[0].upper()
    
    def is_published(self):
        return self.status == 'approved'

# ===== ADD FEEDBACK MODEL HERE (with correct indentation) =====
class Feedback(models.Model):
    """User feedback and suggestions"""
    RATING_CHOICES = [
        (1, '1 - Very Poor'),
        (2, '2 - Poor'),
        (3, '3 - Average'),
        (4, '4 - Good'),
        (5, '5 - Excellent'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='feedbacks'
    )
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    rating = models.IntegerField(choices=RATING_CHOICES, default=5)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Feedback"
    
    def __str__(self):
        return f"{self.subject} - {self.name}"