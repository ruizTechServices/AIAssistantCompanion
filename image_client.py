import os
import logging
import requests
from openai import OpenAI

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def generate_line_art_image(description):
    """Generate a black and white line art image using DALL-E 3."""
    try:
        enhanced_prompt = f"Black and white line art drawing, simple coloring book style: {description}. Clean lines, no shading, suitable for educational worksheets."
        
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=enhanced_prompt,
            n=1,
            size="1024x1024",
            style="natural"
        )
        
        image_url = response.data[0].url
        
        # Download the image
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            return image_response.content
        else:
            raise Exception(f"Failed to download image: {image_response.status_code}")
            
    except Exception as e:
        logging.error(f"Failed to generate image: {e}")
        raise

def save_image(image_data, file_path):
    """Save image data to file."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(image_data)
        return file_path
    except Exception as e:
        logging.error(f"Failed to save image: {e}")
        raise
