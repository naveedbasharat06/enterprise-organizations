import sys, os, requests
sys.path.insert(0, "/app")
os.environ["DJANGO_SETTINGS_MODULE"] = "core.settings"
import django; django.setup()
from accounts.models import User
from rest_framework_simplejwt.tokens import RefreshToken

BASE = "http://localhost:8000/api"

# Generate token for superadmin without needing password
user = User.objects.get(username="superadmin")
refresh = RefreshToken.for_user(user)
token = str(refresh.access_token)
headers = {"Authorization": f"Bearer {token}"}
print("Token generated for:", user.username)

r2 = requests.get(f"{BASE}/roles/", headers=headers)
print("Roles status:", r2.status_code)
roles = r2.json()
print("Roles count:", len(roles))
for ro in roles:
    print(" -", ro.get("name"), "| org:", ro.get("organization_name"))

r3 = requests.post(f"{BASE}/ai/suggest-roles/", json={
    "job_title": "Sales Manager",
    "roles": [ro["name"] for ro in roles]
}, headers=headers)
print("\nSuggest status:", r3.status_code)
print("Suggest resp:", r3.text[:500])
