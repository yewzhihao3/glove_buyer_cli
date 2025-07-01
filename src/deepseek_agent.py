import os
import requests
from dotenv import load_dotenv

PROMPT_PATH = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'deepseek_prompt.txt')

def load_prompt_template():
    with open(PROMPT_PATH, 'r', encoding='utf-8') as f:
        return f.read()

def query_deepseek(hs_code: str, keyword: str) -> str:
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))
    api_key = os.getenv('DEEPSEEK_API_KEY')
    api_url = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')
    if not api_key:
        raise ValueError('DEEPSEEK_API_KEY not found in environment.')
    prompt_template = load_prompt_template()
    prompt = prompt_template.format(hs_code=hs_code, keyword=keyword)
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    response = requests.post(api_url, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    # Extract the model's reply (OpenAI-compatible format)
    return result['choices'][0]['message']['content'] 