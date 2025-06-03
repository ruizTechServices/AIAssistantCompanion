import os
import logging
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.colors import black
from PIL import Image
import io

def create_pdf_from_spec(spec, job_id, images_data=None):
    """Create a PDF worksheet from specification."""
    try:
        # Create directory for this job
        job_dir = f"worksheets/{job_id}"
        os.makedirs(job_dir, exist_ok=True)
        
        pdf_path = f"{job_dir}/worksheet.pdf"
        
        # Create PDF
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        
        # Add title
        c.setFont("Helvetica-Bold", 16)
        title = spec.get("title", "Worksheet")
        c.drawString(50, height - 50, title)
        
        # Add instructions
        if spec.get("instructions"):
            c.setFont("Helvetica", 10)
            instructions = spec["instructions"]
            # Simple text wrapping
            lines = []
            words = instructions.split()
            line = ""
            for word in words:
                if len(line + word) < 80:  # Simple character limit
                    line += word + " "
                else:
                    lines.append(line.strip())
                    line = word + " "
            if line:
                lines.append(line.strip())
            
            y_pos = height - 80
            for line in lines:
                c.drawString(50, y_pos, line)
                y_pos -= 15
        
        # Process elements
        for element in spec.get("elements", []):
            element_type = element.get("type")
            position = element.get("position", {"x": 50, "y": 300})
            x, y = position["x"], height - position["y"]  # Convert to PDF coordinates
            
            if element_type == "text":
                content = element.get("content", "")
                style = element.get("style", {})
                font_size = style.get("fontSize", 12)
                is_bold = style.get("bold", False)
                
                font_name = "Helvetica-Bold" if is_bold else "Helvetica"
                c.setFont(font_name, font_size)
                c.drawString(x, y, content)
                
            elif element_type == "image" and images_data:
                size = element.get("size", {"width": 200, "height": 150})
                # Add placeholder for image
                c.rect(x, y - size["height"], size["width"], size["height"])
                c.drawString(x + 5, y - 10, f"[Image: {element.get('description', 'Image')}]")
                
            elif element_type == "input_field":
                size = element.get("size", {"width": 300, "height": 30})
                placeholder = element.get("placeholder", "")
                
                # Draw input field as rectangle
                c.rect(x, y - size["height"], size["width"], size["height"])
                if placeholder:
                    c.setFont("Helvetica", 10)
                    c.drawString(x + 5, y - size["height"] + 5, placeholder)
        
        c.save()
        return pdf_path
        
    except Exception as e:
        logging.error(f"Failed to create PDF: {e}")
        raise
