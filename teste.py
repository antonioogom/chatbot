import requests

# link do open_weather: https://openweathermap.org/

API_KEY = "04cb9e2dc5857c280e1329316bd6b462"
cidade = "são paulo"
link = f"https://api.openweathermap.org/data/2.5/weather?q={cidade}&appid={API_KEY}&lang=pt_br"

requisicao = requests.get(link)
requisicao_dic = requisicao.json()
descricao = requisicao_dic['weather'][0]['description']
temperatura = round(requisicao_dic['main']['temp'] - 273.15, 2)
print(descricao, f"{temperatura}ºC")