# populate_blogs_success_stories.py
import os
import sys
import django
from django.utils import timezone
from datetime import timedelta

# Setup Django
sys.path.append('C:/Users/dell/jobora')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobora.settings')
django.setup()

from core.models import BlogPost, SuccessStory

def create_blog_posts():
    """Create sample blog posts"""
    blog_posts = [
        {
            'title': 'How to Ace Your Next Technical Interview',
            'category': 'Interview Tips',
            'content': '''
            <h2>Introduction</h2>
            <p>Technical interviews can be daunting, but with the right preparation, you can excel. Here are our top tips:</p>
            
            <h2>1. Master the Fundamentals</h2>
            <p>Ensure you have a strong grasp of data structures and algorithms. Practice common problems on platforms like LeetCode and HackerRank.</p>
            
            <h2>2. Understand the Company</h2>
            <p>Research the company's tech stack and prepare questions about their engineering culture.</p>
            
            <h2>3. Practice Communication</h2>
            <p>Explain your thought process clearly. Interviewers want to see how you approach problems.</p>
            
            <h2>Conclusion</h2>
            <p>With consistent practice and the right mindset, you can succeed in any technical interview.</p>
            ''',
            'image_url': 'https://images.unsplash.com/photo-1611224923853-80b023f02d71?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
            'excerpt': 'Learn essential strategies to prepare for and excel in technical interviews at top tech companies.',
            'is_published': True,
        },
        {
            'title': 'Career Growth Strategies for Software Engineers',
            'category': 'Career Growth',
            'content': '''
            <h2>Building a Successful Career in Tech</h2>
            <p>The path from junior to senior engineer involves more than just technical skills.</p>
            
            <h2>1. Continuous Learning</h2>
            <p>Stay updated with new technologies and frameworks. Attend conferences and participate in online courses.</p>
            
            <h2>2. Mentorship</h2>
            <p>Find mentors who can guide you and seek opportunities to mentor others.</p>
            
            <h2>3. Building Your Brand</h2>
            <p>Contribute to open source, write technical blogs, and speak at meetups.</p>
            
            <h2>Conclusion</h2>
            <p>Career growth is a marathon, not a sprint. Focus on consistent improvement.</p>
            ''',
            'image_url': 'https://images.unsplash.com/photo-1517077304055-6e89abbf09b0?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
            'excerpt': 'Discover proven strategies to accelerate your career growth as a software engineer.',
            'is_published': True,
        },
        {
            'title': 'Writing a Resume That Gets Noticed',
            'category': 'Resume Writing',
            'content': '''
            <h2>Crafting an Effective Resume</h2>
            <p>Your resume is your first impression. Make it count.</p>
            
            <h2>1. Tailor for Each Job</h2>
            <p>Customize your resume for each application. Highlight relevant skills and experiences.</p>
            
            <h2>2. Quantify Achievements</h2>
            <p>Use numbers to demonstrate impact. Instead of "improved performance," say "reduced load time by 40%."</p>
            
            <h2>3. Keep it Clean</h2>
            <p>Use a clean, professional format. Avoid clutter and use bullet points effectively.</p>
            
            <h2>Conclusion</h2>
            <p>A well-crafted resume opens doors. Invest time in making it perfect.</p>
            ''',
            'image_url': 'https://images.unsplash.com/photo-1586281380349-632531db7ed4?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
            'excerpt': 'Learn how to create a compelling resume that stands out to recruiters and hiring managers.',
            'is_published': True,
        },
        {
            'title': 'Navigating Salary Negotiations',
            'category': 'Salary Guide',
            'content': '''
            <h2>Mastering Salary Negotiations</h2>
            <p>Negotiating your salary is a crucial skill that can impact your lifetime earnings.</p>
            
            <h2>1. Do Your Research</h2>
            <p>Know the market rate for your role, experience, and location.</p>
            
            <h2>2. Consider the Whole Package</h2>
            <p>Look beyond base salary. Consider bonuses, equity, benefits, and work flexibility.</p>
            
            <h2>3. Practice Your Pitch</h2>
            <p>Prepare your talking points and practice delivering them confidently.</p>
            
            <h2>Conclusion</h2>
            <p>Approach negotiations as a collaborative discussion, not a confrontation.</p>
            ''',
            'image_url': 'https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
            'excerpt': 'Essential tips for negotiating your salary confidently and getting the compensation you deserve.',
            'is_published': True,
        },
        {
            'title': 'Networking for Career Success',
            'category': 'Networking',
            'content': '''
            <h2>Building Professional Networks</h2>
            <p>Your network can be your most valuable career asset.</p>
            
            <h2>1. Attend Industry Events</h2>
            <p>Participate in conferences, meetups, and workshops in your field.</p>
            
            <h2>2. Use LinkedIn Effectively</h2>
            <p>Build a strong profile, share insights, and connect with professionals in your industry.</p>
            
            <h2>3. Give Before You Ask</h2>
            <p>Offer help and share knowledge before asking for favors.</p>
            
            <h2>Conclusion</h2>
            <p>Networking is about building genuine relationships, not just collecting contacts.</p>
            ''',
            'image_url': 'https://images.unsplash.com/photo-1559136555-9303baea8ebd?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
            'excerpt': 'Learn how to build and maintain a professional network that supports your career growth.',
            'is_published': True,
        },
    ]
    
    created_posts = []
    for post_data in blog_posts:
        post, created = BlogPost.objects.get_or_create(
            title=post_data['title'],
            defaults={
                'category': post_data['category'],
                'content': post_data['content'],
                'image_url': post_data['image_url'],
                'excerpt': post_data['excerpt'],
                'is_published': post_data['is_published'],
            }
        )
        if created:
            created_posts.append(post)
            print(f"✓ Created blog post: {post.title}")
        else:
            print(f"⏭️ Blog post exists: {post.title}")
    
    return created_posts

def create_success_stories():
    """Create sample success stories"""
    success_stories = [
        {
            'full_name': 'Rajesh Kumar',
            'current_role': 'Senior Software Engineer at Google',
            'email': 'rajesh.success@example.com',
            'story_content': '''After months of job searching, I found my dream role through Jobora. The AI matching system perfectly aligned my skills with the right opportunities. Within two weeks of using the platform, I had three interview offers, and I accepted a position at Google. The entire process was seamless!''',
            'status': 'approved',
            'consent': True,
        },
        {
            'full_name': 'Priya Sharma',
            'current_role': 'Product Manager at Amazon',
            'email': 'priya.success@example.com',
            'story_content': '''As a recent MBA graduate, I was struggling to break into product management. Jobora\'s networking features connected me with industry professionals who provided invaluable guidance. I landed a Product Manager role at Amazon, and I couldn\'t be happier with my career trajectory!''',
            'status': 'approved',
            'consent': True,
        },
        {
            'full_name': 'Amit Patel',
            'current_role': 'Data Scientist at Microsoft',
            'email': 'amit.success@example.com',
            'story_content': '''Jobora transformed my job search experience. The smart matching algorithm connected me with companies that truly valued my data science skills. I received personalized recommendations and landed my dream job at Microsoft. The platform\'s career resources were also incredibly helpful!''',
            'status': 'approved',
            'consent': True,
        },
        {
            'full_name': 'Sneha Reddy',
            'current_role': 'UX Designer at Adobe',
            'email': 'sneha.success@example.com',
            'story_content': '''Coming from a non-traditional background, I thought breaking into UX design would be challenging. Jobora\'s portfolio showcase feature helped me display my work effectively, and I connected with hiring managers who appreciated my unique perspective. Now I\'m designing amazing experiences at Adobe!''',
            'status': 'approved',
            'consent': True,
        },
        {
            'full_name': 'Vikram Singh',
            'current_role': 'DevOps Engineer at Netflix',
            'email': 'vikram.success@example.com',
            'story_content': '''The freelance-to-fulltime journey through Jobora was incredible. I started with freelance projects, built my reputation, and was eventually approached by Netflix for a full-time position. The platform\'s credibility system gave companies confidence in my abilities, making the transition smooth and successful.''',
            'status': 'approved',
            'consent': True,
        },
        {
            'full_name': 'Anjali Mehta',
            'current_role': 'Marketing Director at Flipkart',
            'email': 'anjali.success@example.com',
            'story_content': '''After taking a career break, I was nervous about returning to the workforce. Jobora\'s re-entry program and supportive community helped me regain confidence. I updated my skills through their learning resources and landed a leadership role at Flipkart. This platform truly understands career transitions!''',
            'status': 'approved',
            'consent': True,
        },
    ]
    
    created_stories = []
    for story_data in success_stories:
        story, created = SuccessStory.objects.get_or_create(
            full_name=story_data['full_name'],
            current_role=story_data['current_role'],
            defaults={
                'email': story_data['email'],
                'story_content': story_data['story_content'],
                'status': story_data['status'],
                'consent': story_data['consent'],
            }
        )
        if created:
            created_stories.append(story)
            print(f"✓ Created success story: {story.full_name} - {story.current_role}")
        else:
            print(f"⏭️ Success story exists: {story.full_name} - {story.current_role}")
    
    return created_stories

def main():
    print("=" * 60)
    print("JOBORA - BLOG & SUCCESS STORIES POPULATION")
    print("=" * 60)
    
    print("\n1. Creating Blog Posts...")
    blog_posts = create_blog_posts()
    print(f"   Created {len(blog_posts)} blog posts")
    
    print("\n2. Creating Success Stories...")
    success_stories = create_success_stories()
    print(f"   Created {len(success_stories)} success stories")
    
    print("\n" + "=" * 60)
    print("DATA POPULATION COMPLETE!")
    print("=" * 60)
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"   • Blog Posts: {BlogPost.objects.count()}")
    print(f"   • Success Stories: {SuccessStory.objects.count()}")
    print(f"   • Published Stories: {SuccessStory.objects.filter(status='approved').count()}")
    
    print(f"\n🌐 TEST PAGES:")
    print("   • Blog: http://127.0.0.1:8000/blog/")
    print("   • Success Stories: http://127.0.0.1:8000/success-stories/")

if __name__ == '__main__':
    main()