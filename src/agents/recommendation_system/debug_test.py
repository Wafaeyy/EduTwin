import requests

url = "https://en.wikipedia.org/wiki/Machine_learning"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EduTwinRecommendationEngine/1.0"}

try:
    response = requests.get(url, timeout=5, headers=headers)
    print("Status code:", response.status_code)
except requests.exceptions.RequestException as error:
    print("Request failed with error:", error)