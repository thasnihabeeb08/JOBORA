import os
import sys
import django

# Add the parent directory to path so we can import the project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobora.settings')
django.setup()

from jobs.models import Application
from ai.matcher import ResumeJobMatcher
from django.db.models import Q

def run():
    print("=" * 60)
    print("🤖 CALCULATING AI MATCH SCORES FOR ALL APPLICATIONS")
    print("=" * 60)
    
    matcher = ResumeJobMatcher()
    
    # Get all applications without match scores
    applications = Application.objects.filter(
        Q(match_percentage__isnull=True) | Q(match_percentage=0)
    )
    
    total = applications.count()
    print(f"\n📊 Found {total} applications to process\n")
    
    updated = 0
    errors = 0
    
    for i, app in enumerate(applications, 1):
        try:
            print(f"🔄 [{i}/{total}] Processing: {app.candidate.username} - {app.job.title}")
            
            # Calculate scores
            scores = matcher.calculate_final_score(app)
            
            # Update application
            app.rule_score = scores['rule_score']
            app.ai_score = scores['ai_score']
            app.match_percentage = scores['percentage']
            app.save()
            
            print(f"   ✅ Match: {scores['percentage']}% (Rule: {scores['rule_score']}%, AI: {scores['ai_score']}%)")
            updated += 1
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")
            errors += 1
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully updated: {updated} applications")
    print(f"❌ Errors: {errors}")
    print(f"📈 Total processed: {total}")
    print("=" * 60)

if __name__ == "__main__":
    run()