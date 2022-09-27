import requests
from requests.structures import CaseInsensitiveDict

url = "https://graph.facebook.com/v14.0/101728269265418/messages"

headers = CaseInsensitiveDict()
headers["Content-Type"] = "application/json"
headers["Authorization"] = "Bearer EAAIR5bN5iYsBAAUr6OZBpVMcScXBuqWzC2M39ZCHqqNAj5XcRr6wYRZAOZB4ZAtoeucCphFCPSk2xeP9MNroD1PDYMvfhJbFgITneFS3gunTJZCJD5ZAXyl6r4JS5HkhbktO2ZCd6fEoKBeZBzgBIrP17hvhgZBaUmmu8PziOBPbzLTL0vxHsYZBZAeHpsXzZB6RRJOiZA8imeZCteshVx0d7gk5quWPgRVQoWgguUZD"

data = '{ \"messaging_product\": \"whatsapp\", \"to\": \"5511987408516\", \"type\": \"template\", \"template\": { \"name\": \"hello_world\", \"language\": { \"code\": \"en_US\" } } }'


resp = requests.post(url, headers=headers, data=data)

print(resp.status_code)