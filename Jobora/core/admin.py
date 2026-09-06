from django.contrib import admin
from .models import BlogPost, SuccessStory

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'date_posted', 'is_published']
    list_filter = ['category', 'date_posted', 'is_published']
    search_fields = ['title', 'content', 'excerpt']
    list_editable = ['is_published']  # Easy publish/unpublish from list view

@admin.register(SuccessStory)
class SuccessStoryAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'current_role', 'email', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['full_name', 'current_role', 'email', 'story_content']
    list_editable = ['status']  # Allows quick status changes from list view
    readonly_fields = ['created_at', 'updated_at']
    actions = ['approve_stories', 'reject_stories']
    
    fieldsets = (
        ('Story Information', {
            'fields': ('full_name', 'current_role', 'email', 'story_content', 'consent')
        }),
        ('Moderation', {
            'fields': ('status', 'approved_by', 'created_at', 'updated_at')
        }),
    )
    
    def approve_stories(self, request, queryset):
        updated = queryset.update(status='approved', approved_by=request.user)
        self.message_user(request, f'{updated} success stories approved successfully.')
    
    def reject_stories(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} success stories rejected.')
    
    approve_stories.short_description = "Approve selected stories"
    reject_stories.short_description = "Reject selected stories"
    
    # Auto-set approved_by when saving from admin
    def save_model(self, request, obj, form, change):
        if obj.status == 'approved' and not obj.approved_by:
            obj.approved_by = request.user
        super().save_model(request, obj, form, change)