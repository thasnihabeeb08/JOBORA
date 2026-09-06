# jobs/admin.py - REPLACE ENTIRE FILE WITH THIS
from django.contrib import admin
from .models import JobCategory, Job, Application, Interview, Message, CompanyAnalytics

# DO NOT REGISTER Company HERE - It's already in users/admin.py

@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'job_type', 'location', 'is_active', 'is_approved', 'posted_on')
    list_filter = ('job_type', 'is_active', 'is_approved', 'posted_on', 'category')
    search_fields = ('title', 'company__name', 'location')
    readonly_fields = ('posted_on', 'updated_on', 'views_count')
    list_editable = ('is_active', 'is_approved')

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'job', 'status', 'applied_on')
    list_filter = ('status', 'applied_on', 'job__company')
    search_fields = ('candidate__username', 'job__title', 'cover_letter')
    readonly_fields = ('applied_on', 'shortlisted_on', 'updated_on')

@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ('application', 'scheduled_date', 'interview_type', 'status', 'interviewer')
    list_filter = ('status', 'interview_type', 'scheduled_date')
    search_fields = ('application__job__title', 'interviewer')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'subject', 'is_read', 'sent_at')
    list_filter = ('is_read', 'sent_at')
    search_fields = ('subject', 'sender__username', 'recipient__username')
    readonly_fields = ('sent_at',)

@admin.register(CompanyAnalytics)
class CompanyAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('company', 'total_applications', 'total_hires', 'application_conversion', 'last_updated')
    readonly_fields = ('total_job_views', 'total_applications', 'total_hires', 'avg_time_to_hire', 'application_conversion', 'last_updated')