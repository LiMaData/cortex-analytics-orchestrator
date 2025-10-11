import os
import requests
from dotenv import load_dotenv

load_dotenv()

BING_API_KEY = os.getenv("BING_API_KEY")
BING_ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"

def web_search(query: str, count: int = 5):
  """Search the web using Bing Search API"""
  headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY}
  params = {"q": query, "count": count}
  response = requests.get(BING_ENDPOINT, headers=headers, params=params)
  response.raise_for_status()
  results = response.json()

  return [
      {
          "title": item["name"],
          "snippet": item["snippet"],
          "url": item["url"]
      }
      for item in results.get("webPages", {}).get("value", [])
  ]