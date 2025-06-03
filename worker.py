import threading
import logging
from app import db
from models import Worksheet
from llm_client import generate_worksheet_spec
from image_client import generate_line_art_image, save_image
from pdf_generator import create_pdf_from_spec
from interactive_generator import generate_interactive_html

def start_generation_job(job_id):
    """Start background thread for worksheet generation."""
    thread = threading.Thread(target=run_generation_job, args=(job_id,))
    thread.daemon = True
    thread.start()

def run_generation_job(job_id):
    """Background job to generate worksheet."""
    try:
        with db.app.app_context():  # Create application context
            # Update status to in_progress
            worksheet = Worksheet.query.get(job_id)
            if not worksheet:
                logging.error(f"Worksheet {job_id} not found")
                return
            
            worksheet.status = "in_progress"
            db.session.commit()
            
            # Generate worksheet specification
            logging.info(f"Generating worksheet spec for {job_id}")
            spec = generate_worksheet_spec(worksheet.prompt_json)
            
            # Generate images if needed
            images_data = {}
            if worksheet.prompt_json.get("imagesAllowed", False):
                for element in spec.get("elements", []):
                    if element.get("type") == "image":
                        description = element.get("description", "")
                        if description:
                            try:
                                logging.info(f"Generating image: {description}")
                                image_data = generate_line_art_image(description)
                                image_path = f"worksheets/{job_id}/image_{len(images_data)}.png"
                                save_image(image_data, image_path)
                                images_data[description] = image_path
                            except Exception as e:
                                logging.error(f"Failed to generate image: {e}")
                                # Continue without this image
            
            # Generate PDF
            logging.info(f"Generating PDF for {job_id}")
            pdf_path = create_pdf_from_spec(spec, job_id, images_data)
            
            # Generate interactive HTML
            logging.info(f"Generating interactive HTML for {job_id}")
            html_path = generate_interactive_html(spec, job_id, images_data)
            
            # Update worksheet record
            worksheet.status = "done"
            worksheet.pdf_path = pdf_path
            worksheet.interactive_path = html_path
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
