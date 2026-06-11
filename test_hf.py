import sys, os
sys.path.insert(0, "/app")
os.environ["DJANGO_SETTINGS_MODULE"] = "core.settings"
import django; django.setup()
from django.conf import settings
import requests

api_key = settings.HUGGINGFACE_API_KEY
resp = requests.post(
    "https://router.huggingface.co/together/v1/chat/completions",
    headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
    json={
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "messages": [{"role": "user", "content": "Reply only with this exact JSON: {\"suggestions\":[\"Admin\"],\"reason\":\"test\"}"}],
        "max_tokens": 50,
        "temperature": 0.3
    },
    timeout=30
)
print("Status:", resp.status_code)
print("Body:", resp.text[:300])
