from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')), 
    path('users/', include('users.urls')),
    path('company/', include('jobs.urls')),
    path('job-seeker/', include('job_seeker.urls')),
    path('admin-panel/', include('admin_panel.urls')),
]

# ========== DEBUG TOOLBAR URLs - SAFELY REMOVED (COMMENTED OUT) ==========
# if settings.DEBUG:
#     import debug_toolbar
#     urlpatterns = [
#         path('__debug__/', include(debug_toolbar.urls)),
#     ] + urlpatterns

# ========== MEDIA & STATIC FILES SERVING IN DEVELOPMENT ==========
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)