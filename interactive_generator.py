import os
import json
import logging
from jinja2 import Template

def generate_interactive_html(spec, job_id, images_data=None):
    """Generate interactive HTML version of the worksheet."""
    try:
        # Create directory for this job
        job_dir = f"worksheets/{job_id}"
        os.makedirs(job_dir, exist_ok=True)
        
        html_path = f"{job_dir}/interactive.html"
        
        # Read template
        with open("templates/interactive_template.html", "r") as f:
            template_content = f.read()
        
        template = Template(template_content)
        
        # Render HTML
        html_content = template.render(
            title=spec.get("title", "Interactive Worksheet"),
            instructions=spec.get("instructions", ""),
            elements=spec.get("elements", []),
            job_id=job_id
        )
        
        # Write HTML file
        with open(html_path, "w") as f:
            f.write(html_content)
        
        return html_path
        
    except Exception as e:
        logging.error(f"Failed to create interactive HTML: {e}")
        raise
