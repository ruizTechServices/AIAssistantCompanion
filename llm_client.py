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
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logging.error(f"Failed to generate embedding: {e}")
        raise

def generate_worksheet_spec(prompt_data):
    """Generate worksheet specification using GPT-4o."""
    try:
        system_prompt = """You are an expert educational content creator. Generate a detailed worksheet specification in JSON format.

The worksheet should be appropriate for the specified grade level and topic, with engaging activities and clear instructions.

Return a JSON object with the following structure:
{
    "title": "Worksheet Title",
    "instructions": "General instructions for the worksheet",
    "elements": [
        {
            "type": "text",
            "content": "Text content or question",
            "position": {"x": 50, "y": 100},
            "style": {"fontSize": 12, "bold": false}
        },
        {
            "type": "image",
            "description": "Description for image generation",
            "position": {"x": 200, "y": 150},
            "size": {"width": 200, "height": 150}
        },
        {
            "type": "input_field",
            "placeholder": "Answer space",
            "position": {"x": 50, "y": 200},
            "size": {"width": 300, "height": 30}
        }
    ]
}

Keep the layout within 612x792 points (standard letter size). Include appropriate spacing and clear visual hierarchy."""

        user_prompt = f"""Create a worksheet with the following specifications:
- Grade Level: {prompt_data['gradeLevel']}
- Topic: {prompt_data['topic']}
- Activities: {prompt_data['activities']}
- Style: {prompt_data['style']}
- Images Allowed: {prompt_data['imagesAllowed']}

Generate a complete worksheet specification in JSON format."""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            timeout=30  # 30 second timeout
        )
        
        return json.loads(response.choices[0].message.content)
    
    except Exception as e:
        logging.error(f"Failed to generate worksheet spec: {e}")
        raise
