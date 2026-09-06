from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
      path('about/', views.about, name='about'), 
      path('contact/', views.contact, name='contact'),
      path('blog/', views.blog, name='blog'),
      path('blog/<int:post_id>/', views.blog_post_detail, name='blog_post_detail'),
         path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('security/', views.security, name='security'),
    path('success-stories/', views.success_stories, name='success_stories'),
    path('submit-success-story/', views.submit_success_story, name='submit_success_story'),
    path('safe-job-search/', views.safe_job_search, name='safe_job_search'),
    path('feedback/', views.feedback, name='feedback'),
]