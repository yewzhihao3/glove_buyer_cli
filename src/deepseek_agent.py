import os
import requests
from dotenv import load_dotenv
import re

PROMPT_PATH = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'deepseek_prompt.txt')

def load_prompt_template():
    with open(PROMPT_PATH, 'r', encoding='utf-8') as f:
        return f.read()

def is_multipart_response(response: str) -> bool:
    """Detect if the response is part of a multi-part answer (e.g., contains 'Part 1', 'Part 2', etc.)."""
    return bool(re.search(r'Part\s*\d+', response, re.IGNORECASE))

def get_next_part_prompt(original_prompt: str, part_number: int) -> str:
    """Generate a follow-up prompt to request the next part of the answer."""
    return f"{original_prompt}\n\nPlease continue with Part {part_number}. Only return the next part of the list, do not repeat previous results."

def query_deepseek(hs_code: str, keyword: str, country: str) -> str:
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))
    api_key = os.getenv('DEEPSEEK_API_KEY')
    api_url = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')
    if not api_key:
        raise ValueError('DEEPSEEK_API_KEY not found in environment.')
    prompt_template = load_prompt_template()
    prompt = prompt_template.format(hs_code=hs_code, keyword=keyword, country=country)
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    data = {
        "model": "deepseek-reasoner",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    all_parts = []
    part_number = 1
    while True:
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        content = result['choices'][0]['message']['content']
        all_parts.append(content)
        # Check if this part indicates there is a next part
        if re.search(rf'Part\s*{part_number}', content, re.IGNORECASE):
            # Look for explicit end or next part
            if re.search(rf'Part\s*{part_number + 1}', content, re.IGNORECASE):
                # The model already included the next part, so break
                break
            # Prepare to fetch the next part
            part_number += 1
            next_prompt = get_next_part_prompt(prompt, part_number)
            data["messages"] = [
                {"role": "user", "content": next_prompt}
            ]
        else:
            break
    return '\n'.join(all_parts) 