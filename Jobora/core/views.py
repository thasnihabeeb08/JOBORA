from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import BlogPost, SuccessStory, Feedback
from .forms import SuccessStoryForm, FeedbackForm

def homepage(request):
    return render(request, 'homepage.html')

def about(request):
    return render(request, 'about.html')  

def contact(request):
    return render(request, 'contact.html')

def blog(request):
    # Get category filter from URL
    category = request.GET.get('category', '')
    
    # Filter posts by category if specified
    if category:
        posts_list = BlogPost.objects.filter(category=category, is_published=True).order_by('-date_posted')
    else:
        posts_list = BlogPost.objects.filter(is_published=True).order_by('-date_posted')
    
    # Pagination - show 10 posts per page
    paginator = Paginator(posts_list, 10)
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)
    
    # Calculate page range for pagination buttons (show max 5 pages)
    page_range = []
    for num in page_obj.paginator.page_range:
        if num <= 3 or num > page_obj.paginator.num_pages - 2 or abs(num - page_obj.number) <= 1:
            page_range.append(num)
        elif page_range[-1] != '...':
            page_range.append('...')
    
    context = {
        'posts': page_obj,
        'page_obj': page_obj,
        'current_category': category,
        'page_range': page_range,
    }
    
    return render(request, 'blog.html', context)

def blog_post_detail(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id, is_published=True)
    
    # Get related posts (same category, exclude current post)
    related_posts = BlogPost.objects.filter(
        category=post.category, 
        is_published=True
    ).exclude(id=post.id).order_by('-date_posted')[:3]
    
    # If not enough related posts, get latest posts
    if related_posts.count() < 3:
        additional_posts = BlogPost.objects.filter(
            is_published=True
        ).exclude(id=post.id).exclude(id__in=[p.id for p in related_posts]).order_by('-date_posted')[:3-related_posts.count()]
        related_posts = list(related_posts) + list(additional_posts)
    
    context = {
        'post': post,
        'related_posts': related_posts,
    }
    
    return render(request, 'blog_post_detail.html', context)

def terms(request):
    return render(request, 'terms.html')

def privacy(request):
    return render(request, 'privacy.html')

def security(request):
    return render(request, 'security.html')

# ===== SUCCESS STORIES VIEWS =====
def success_stories(request):
    # Get only approved stories for public view
    stories = SuccessStory.objects.filter(status='approved').order_by('-created_at')
    
    context = {
        'stories': stories,
        'form': SuccessStoryForm()  # Empty form for GET requests
    }
    return render(request, 'success_stories.html', context)

def submit_success_story(request):
    if request.method == 'POST':
        form = SuccessStoryForm(request.POST)
        if form.is_valid():
            success_story = form.save(commit=False)
            # Set status to pending by default
            success_story.status = 'pending'
            success_story.save()
            
            messages.success(request, 'Thank you for sharing your story! It has been submitted for review. We will notify you once it\'s published.')
            return redirect('success_stories')
        else:
            # If form is invalid, return to the page with error messages
            stories = SuccessStory.objects.filter(status='approved')
            context = {
                'stories': stories,
                'form': form
            }
            messages.error(request, 'Please correct the errors below.')
            return render(request, 'success_stories.html', context)
    
    # If not POST, redirect to success stories page
    return redirect('success_stories')

def safe_job_search(request):
    """Safe Job Search Guidelines Page"""
    context = {
        'title': 'Safe Job Search Guidelines - Jobora',
        'page_description': 'Protect yourself from job scams and find legitimate opportunities with confidence',
        'active_page': 'safe_job_search'
    }
    return render(request, 'safe_job_search.html', context)

# ===== NEW FEEDBACK VIEW =====
def feedback(request):
    """Submit feedback"""
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            # If user is logged in, associate feedback with user
            if request.user.is_authenticated:
                feedback.user = request.user
            feedback.save()
            messages.success(request, 'Thank you for your feedback! We appreciate your input.')
            return redirect('homepage')
    else:
        # Pre-fill form if user is logged in
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'name': request.user.get_full_name() or request.user.username,
                'email': request.user.email,
            }
        form = FeedbackForm(initial=initial_data)
    
    return render(request, 'feedback.html', {'form': form})