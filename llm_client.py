import json
import os
import logging
from openai import OpenAI

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def generate_embedding(text):
    """Generate embedding for text using OpenAI."""
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logging.error(f"Failed to generate embedding: {e}")
        raise

def generate_worksheet_spec(prompt_data):
    """Generate worksheet specification using OpenAI."""
    try:
        prompt = f"""Create a detailed educational worksheet specification in JSON format for:
- Grade Level: {prompt_data['gradeLevel']}
- Topic: {prompt_data['topic']}
- Activities: {prompt_data['activities']}
- Style: {prompt_data['style']}
- Images Allowed: {prompt_data['imagesAllowed']}

Return a JSON object with this exact structure:
{{
    "title": "Worksheet Title",
    "instructions": "General instructions for the worksheet",
    "elements": [
        {{
            "type": "text",
            "content": "Text content or question",
            "position": {{"x": 50, "y": 100}},
            "style": {{"fontSize": 12, "bold": false}}
        }},
        {{
            "type": "input_field",
            "placeholder": "Answer space",
            "position": {{"x": 50, "y": 200}},
            "size": {{"width": 300, "height": 30}}
        }}
    ]
}}

Keep layout within 612x792 points (letter size). Include 5-10 educational elements."""

        response = openai_client.responses.create(
            model="gpt-4.1",
            input=prompt
        )
        
        # Parse the JSON from the response
        import re
        json_match = re.search(r'\{.*\}', response.output_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            raise Exception("No valid JSON found in response")
    
    except Exception as e:
        logging.error(f"Failed to generate worksheet spec: {e}")
        raise
