import threading
import logging

# Supabase client for uploading generated files
try:
    from supabase_client import supabase
except Exception as e:  # Supabase may not be configured in dev
    supabase = None
    logging.warning(f"Supabase client not available: {e}")

def upload_to_supabase(local_path: str, remote_path: str) -> str:
    """Upload a file to Supabase Storage and return the public URL."""
    if not supabase:
        return local_path
    try:
        with open(local_path, "rb") as f:
            supabase.storage.from_("worksheets").upload(remote_path, f, upsert=True)
        public_url = supabase.storage.from_("worksheets").get_public_url(remote_path)
        return public_url
    except Exception as e:
        logging.error(f"Failed to upload {local_path} to Supabase: {e}")
        return local_path

def start_generation_job(job_id):
    """Start background thread for worksheet generation."""
    logging.info(f"Starting generation thread for job {job_id}")
    thread = threading.Thread(target=run_generation_job, args=(job_id,))
    thread.daemon = True
    thread.start()
    logging.info(f"Thread started for job {job_id}")

def run_generation_job(job_id):
    """Background job to generate worksheet."""
    import os
    import sys
    
    # Add current directory to path to ensure imports work
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    try:
        logging.info(f"Worker thread executing for job {job_id}")
        
        # Import everything inside the function to avoid circular imports
        from app import app, db
        from models import Worksheet  
        from llm_client import generate_worksheet_spec
        from image_client import generate_line_art_image, save_image
        from pdf_generator import create_pdf_from_spec
        from interactive_generator import generate_interactive_html
        
        with app.app_context():
            logging.info(f"App context created for job {job_id}")
            
            # Update status to in_progress
            worksheet = Worksheet.query.get(job_id)
            if not worksheet:
                logging.error(f"Worksheet {job_id} not found in database")
                return
            
            logging.info(f"Found worksheet {job_id}, updating status to in_progress")
            worksheet.status = "in_progress"
            worksheet.progress_step = "Starting generation"
            worksheet.progress_percent = 5
            db.session.commit()
            
            # Check for cancellation
            if worksheet.status == "cancelled":
                logging.info(f"Job {job_id} was cancelled")
                return
            
            # Generate worksheet specification
            logging.info(f"Step 1/4: Generating worksheet specification for {job_id}")
            worksheet.progress_step = "Generating content with AI"
            worksheet.progress_percent = 20
            db.session.commit()
            
            spec = generate_worksheet_spec(worksheet.prompt_json)
            logging.info(f"Generated worksheet spec with {len(spec.get('elements', []))} elements")
            
            worksheet.progress_percent = 40
            db.session.commit()
            
            # Generate images if needed
            logging.info(f"Step 2/4: Processing images for {job_id}")
            images_data = {}
            if worksheet.prompt_json.get("imagesAllowed", False):
                image_elements = [e for e in spec.get("elements", []) if e.get("type") == "image"]
                logging.info(f"Found {len(image_elements)} images to generate")
                for i, element in enumerate(image_elements):
                    description = element.get("description", "")
                    if description:
                        try:
                            logging.info(f"Generating image {i+1}/{len(image_elements)}: {description}")
                            image_data = generate_line_art_image(description)
                            image_path = f"worksheets/{job_id}/image_{len(images_data)}.png"
                            save_image(image_data, image_path)
                            images_data[description] = image_path
                            logging.info(f"Successfully generated image: {image_path}")
                        except Exception as e:
                            logging.error(f"Failed to generate image: {e}")
                            # Continue without this image
            else:
                logging.info("Images disabled, skipping image generation")
            
            # Generate PDF
            logging.info(f"Step 3/4: Generating PDF for {job_id}")
            pdf_path = create_pdf_from_spec(spec, job_id, images_data)
            logging.info(f"PDF generated: {pdf_path}")
            pdf_url = upload_to_supabase(pdf_path, f"{job_id}/worksheet.pdf")
            logging.info(f"PDF uploaded to: {pdf_url}")
            
            # Generate interactive HTML
            logging.info(f"Step 4/4: Generating interactive HTML for {job_id}")
            html_path = generate_interactive_html(spec, job_id, images_data)
            logging.info(f"Interactive HTML generated: {html_path}")
            html_url = upload_to_supabase(html_path, f"{job_id}/interactive.html")
            logging.info(f"HTML uploaded to: {html_url}")
            
            # Update worksheet record
            worksheet.status = "done"
            worksheet.pdf_path = pdf_url
            worksheet.interactive_path = html_url
            db.session.commit()
            
            logging.info(f"Successfully completed worksheet generation for {job_id}")
            
    except Exception as e:
        logging.error(f"Error generating worksheet {job_id}: {e}")
        try:
            with db.app.app_context():
                worksheet = Worksheet.query.get(job_id)
                if worksheet:
                    worksheet.status = "error"
                    worksheet.error_message = str(e)
                    db.session.commit()
        except Exception as db_error:
            logging.error(f"Failed to update error status: {db_error}")
