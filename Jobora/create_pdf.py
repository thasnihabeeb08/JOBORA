from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
import os

def create_safety_pdf():
    """Create a professional Jobora Safety Handbook PDF"""
    
    # Ensure directory exists
    pdf_dir = "core/static/pdf"
    os.makedirs(pdf_dir, exist_ok=True)
    
    pdf_path = os.path.join(pdf_dir, "jobora_safety_handbook.pdf")
    
    # Create PDF
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(colors.HexColor("#2563EB"))  # Jobora blue
    c.drawCentredString(width/2, height - 100, "Jobora Safety Handbook")
    
    # Subtitle
    c.setFont("Helvetica", 14)
    c.setFillColor(colors.grey)
    c.drawCentredString(width/2, height - 130, "Essential Guidelines for Safe Job Searching")
    
    # Content
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    
    # Guidelines
    guidelines = [
        "1. Always verify company details before applying",
        "2. Never share sensitive information like bank details",
        "3. Be cautious of jobs requiring upfront payments",
        "4. Verify interviewers' identities and locations",
        "5. Report suspicious job postings immediately",
        "6. Use secure connections for applications",
        "7. Research companies on multiple platforms",
        "8. Trust your instincts - if too good to be true, it probably is",
    ]
    
    y = height - 180
    for guideline in guidelines:
        c.drawString(72, y, guideline)
        y -= 25
    
    # Red Flags section
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.HexColor("#DC2626"))  # Red
    c.drawString(72, y - 30, "Common Job Scam Red Flags:")
    
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.black)
    
    red_flags = [
        "• Unsolicited job offers with overly generous terms",
        "• Requests for upfront payments or 'registration fees'",
        "• Vague job descriptions or unclear company info",
        "• High salaries for minimal qualifications",
        "• Pressure to act quickly",
        "• Text-only interviews without video calls",
    ]
    
    y = y - 60
    for flag in red_flags:
        c.drawString(85, y, flag)
        y -= 20
    
    # Contact info
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColor(colors.blue)
    c.drawCentredString(width/2, 100, "Jobora AI-Powered Recruitment System")
    c.drawCentredString(width/2, 85, "Safety First, Always")
    
    c.drawCentredString(width/2, 60, "Contact Safety Team: safety@jobora.ai")
    c.drawCentredString(width/2, 45, "Report Issues: jobora.ai/report-scam")
    
    # Save PDF
    c.save()
    
    print(f"✓ PDF created successfully at: {pdf_path}")
    print(f"✓ File size: {os.path.getsize(pdf_path)} bytes")
    
    # Verify it's a valid PDF
    with open(pdf_path, 'rb') as f:
        header = f.read(5).decode('ascii', errors='ignore')
        print(f"✓ PDF Header: {header}")
    
    return pdf_path

if __name__ == "__main__":
    create_safety_pdf()