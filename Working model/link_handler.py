import os
import requests

# Set up Google Custom Search API credentials
GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
GOOGLE_CSE_ID = os.environ['GOOGLE_CSE_ID']

def get_related_links(query):
    # Use the Google Custom Search API to search for related links
    url = 'https://www.googleapis.com/customsearch/v1'
    params = {'q': query, 'num': 10, 'key': GOOGLE_API_KEY, 'cx': GOOGLE_CSE_ID}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        results = response.json().get('items', [])
        if results:
            links = []
            for result in results:
                if result.get('link'):
                    links.append(result['link'])
            return '\n\n'.join(links)
        else:
            return None
    else:
        return None
