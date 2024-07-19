import requests
from urllib.parse import urlencode

proxy_params = {
      'api_key': '',
      'url': 'https://www.carjam.co.nz/car/?plate=UA100/', 
  }

response = requests.get(
  url='https://proxy.scrapeops.io/v1/',
  params=urlencode(proxy_params),
  timeout=120,
)
with open('temp.html', 'w', encoding='utf-8') as file:
    file.write(response.text)

# print('Body: ', response.content)
