from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Company, SavedJob

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Job Seeker Profile'
    fk_name = 'user'
    max_num = 1
    min_num = 1
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('phone', 'location', 'date_of_birth', 'profile_picture')
        }),
        ('Professional', {
            'fields': ('headline', 'summary', 'user_type', 'skills')
        }),
        ('Documents', {
            'fields': ('resume',)
        }),
        ('Status', {
            'fields': ('is_profile_complete', 'is_verified', 'is_active_seeker')
        }),
    )

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'date_joined')
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'location', 'user_type', 'is_profile_complete', 'is_verified')
    list_filter = ('user_type', 'is_profile_complete', 'is_verified', 'is_active_seeker', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone', 'location', 'skills')
    readonly_fields = ('created_at', 'updated_at', 'get_completion_percentage')
    
    def get_completion_percentage(self, obj):
        return f"{obj.completion_percentage}%" if hasattr(obj, 'completion_percentage') else "N/A"
    get_completion_percentage.short_description = 'Profile Completion %'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': ('phone', 'location', 'date_of_birth', 'profile_picture')
        }),
        ('Professional Information', {
            'fields': ('headline', 'summary', 'user_type', 'skills')
        }),
        ('Documents', {
            'fields': ('resume',)
        }),
        ('Status', {
            'fields': ('is_profile_complete', 'is_verified', 'is_active_seeker')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_verified', 'mark_as_complete']
    
    def mark_as_verified(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, f"{queryset.count()} profiles marked as verified.")
    mark_as_verified.short_description = "Mark selected profiles as verified"
    
    def mark_as_complete(self, request, queryset):
        queryset.update(is_profile_complete=True)
        self.message_user(request, f"{queryset.count()} profiles marked as complete.")
    mark_as_complete.short_description = "Mark selected profiles as complete"

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry', 'location', 'contact_person', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'industry', 'created_at')
    search_fields = ('name', 'contact_person', 'location', 'email', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_approved',)
    actions = ['approve_companies', 'disapprove_companies']
    
    fieldsets = (
        ('Company Information', {
            'fields': ('user', 'name', 'contact_person', 'phone', 'location', 'industry')
        }),
        ('Company Details', {
            'fields': ('email', 'description', 'logo')
        }),
        ('Verification', {
            'fields': ('is_approved',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def approve_companies(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"{queryset.count()} companies approved.")
    approve_companies.short_description = "Approve selected companies"
    
    def disapprove_companies(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f"{queryset.count()} companies disapproved.")
    disapprove_companies.short_description = "Disapprove selected companies"

@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ('user', 'job_title', 'company_name', 'saved_at', 'is_active')
    list_filter = ('is_active', 'saved_at', 'created_at')
    search_fields = ('user__username', 'job__title', 'job__company__name')
    readonly_fields = ('saved_at', 'created_at', 'updated_at')
    
    def job_title(self, obj):
        return obj.job.title
    job_title.short_description = 'Job Title'
    
    def company_name(self, obj):
        return obj.job.company.name if obj.job.company else 'N/A'
    company_name.short_description = 'Company'

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.site_header = "Jobora Administration"
admin.site.site_title = "Jobora Admin Portal"
admin.site.index_title = "Welcome to Jobora Admin Portal"