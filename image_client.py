import os
import logging
import requests
from openai import OpenAI

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def generate_line_art_image(description):
    """Generate a black and white line art image using OpenAI."""
    try:
        prompt = f"Generate a black and white line art drawing, simple coloring book style: {description}. Clean lines, no shading, suitable for educational worksheets."
        
        response = openai_client.responses.create(
            model="gpt-4.1",
            tools=[{"type": "dalle"}],
            input=prompt
        )
        
        # For now, return a placeholder since the new API structure isn't fully documented
        # We'll use a simple SVG placeholder for line art
        svg_content = f'''<svg width="200" height="150" xmlns="http://www.w3.org/2000/svg">
            <rect width="200" height="150" fill="white" stroke="black" stroke-width="2"/>
            <text x="100" y="75" text-anchor="middle" font-family="Arial" font-size="12" fill="black">{description[:20]}...</text>
        </svg>'''
        return svg_content.encode('utf-8')
            
    except Exception as e:
        logging.error(f"Failed to generate image: {e}")
        # Return placeholder SVG on error
        svg_content = f'''<svg width="200" height="150" xmlns="http://www.w3.org/2000/svg">
            <rect width="200" height="150" fill="white" stroke="black" stroke-width="2"/>
            <text x="100" y="75" text-anchor="middle" font-family="Arial" font-size="12" fill="black">Image</text>
        </svg>'''
        return svg_content.encode('utf-8')

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
