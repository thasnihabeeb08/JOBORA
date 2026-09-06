import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
import docx

class ResumeJobMatcher:
    """Simple AI-powered resume-job matching"""
    
    def extract_text_from_resume(self, resume_file):
        """Extract text from resume file"""
        text = ""
        try:
            # For text files
            if resume_file.name.endswith('.txt'):
                resume_file.seek(0)
                text = resume_file.read().decode('utf-8')
                print(f"✅ Extracted text from {resume_file.name}: {len(text)} chars")
                
            # For PDF files
            elif resume_file.name.endswith('.pdf'):
                pdf_reader = PyPDF2.PdfReader(resume_file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text() or ""
                    text += page_text
                print(f"✅ Extracted PDF text: {len(text)} chars")
            
            # For Word files
            elif resume_file.name.endswith('.docx'):
                doc = docx.Document(resume_file)
                for para in doc.paragraphs:
                    text += para.text + "\n"
                print(f"✅ Extracted DOCX text: {len(text)} chars")
            
            return text
        except Exception as e:
            print(f"❌ Error extracting text: {e}")
            return ""
    
    def calculate_ai_similarity(self, resume_text, job_description):
        """Calculate similarity between resume and job description"""
        if not resume_text or not job_description:
            return 0.0
        
        try:
            # Create TF-IDF vectors
            vectorizer = TfidfVectorizer(max_features=500, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform([resume_text, job_description])
            
            # Calculate similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
            return round(float(similarity[0][0]) * 100, 2)
        except Exception as e:
            print(f"AI similarity error: {e}")
            return 0.0
    
    def calculate_rule_score(self, application):
        """Simple rule-based score"""
        score = 0
        job = application.job
        
        try:
            profile = application.candidate.profile
            
            # Skills match (40 points)
            if profile.skills and job.skills_required:
                profile_skills = set([s.strip().lower() for s in profile.skills.split(',') if s.strip()])
                job_skills = set([s.strip().lower() for s in job.skills_required.split(',') if s.strip()])
                if job_skills:
                    matched = len(profile_skills.intersection(job_skills))
                    total = len(job_skills)
                    if total > 0:
                        score += (matched / total) * 40
            
            # Experience match (20 points)
            if profile.years_experience is not None and job.experience_level:
                if job.experience_level == 'fresher' and profile.years_experience <= 1:
                    score += 20
                elif job.experience_level == 'junior' and 1 <= profile.years_experience <= 3:
                    score += 20
                elif job.experience_level == 'mid' and 3 <= profile.years_experience <= 6:
                    score += 20
                elif job.experience_level == 'senior' and profile.years_experience >= 6:
                    score += 20
                elif job.experience_level == 'executive' and profile.years_experience >= 10:
                    score += 20
            
            # Location match (20 points)
            if profile.location and job.location:
                if profile.location.lower() == job.location.lower():
                    score += 20
                elif job.is_remote:
                    score += 15
            
            # Job type match (20 points)
            if profile.preferred_job_types and job.job_type:
                if job.job_type in profile.preferred_job_types:
                    score += 20
            
            return min(score, 100)
        except Exception as e:
            print(f"Rule score error: {e}")
            return 0
    
    def calculate_final_score(self, application):
        """Final score = 70% rule + 30% AI"""
        rule_score = self.calculate_rule_score(application)
        
        # Get resume text
        resume_text = ""
        if application.resume:
            try:
                resume_text = self.extract_text_from_resume(application.resume)
            except Exception as e:
                print(f"Resume extraction error: {e}")
        
        job_desc = application.job.description or ""
        ai_score = self.calculate_ai_similarity(resume_text, job_desc)
        
        # Hybrid formula
        final_score = (rule_score * 0.7) + (ai_score * 0.3)
        
        return {
            'rule_score': round(rule_score, 2),
            'ai_score': ai_score,
            'final_score': round(final_score, 2),
            'percentage': int(final_score)
        }