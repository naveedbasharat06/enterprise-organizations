import sys, requests

BASE = "http://localhost:8080/api"

# Login first
r = requests.post(f"{BASE}/auth/login/", json={"username": "superadmin", "password": "admin123"})
print("Login status:", r.status_code)
if r.status_code != 200:
    print("Login failed:", r.text)
    sys.exit(1)

token = r.json().get("access")
print("Got token:", token[:20] + "...")

headers = {"Authorization": f"Bearer {token}"}

# Fetch roles
r2 = requests.get(f"{BASE}/roles/", headers=headers)
print("\nRoles status:", r2.status_code)
print("Roles:", r2.json())

# Test suggest
r3 = requests.post(f"{BASE}/ai/suggest-roles/", json={
    "job_title": "Sales Manager",
    "roles": ["marketing research", "Template designing"]
}, headers=headers)
print("\nSuggest status:", r3.status_code)
print("Suggest response:", r3.text[:500])
