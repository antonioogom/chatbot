from flask import Flask, render_template
import requests
from requests.structures import CaseInsensitiveDict

app = Flask(__name__)

@app.route("/")
def homepage():
    return render_template("homepage.html")

@app.route("/contatos")
def contatos():
    return render_template("contatos.html")

@app.route("/post")
def post():
    url = "https://graph.facebook.com/v14.0/101728269265418/messages"

    headers = CaseInsensitiveDict()
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = "Bearer EAAIR5bN5iYsBAAUr6OZBpVMcScXBuqWzC2M39ZCHqqNAj5XcRr6wYRZAOZB4ZAtoeucCphFCPSk2xeP9MNroD1PDYMvfhJbFgITneFS3gunTJZCJD5ZAXyl6r4JS5HkhbktO2ZCd6fEoKBeZBzgBIrP17hvhgZBaUmmu8PziOBPbzLTL0vxHsYZBZAeHpsXzZB6RRJOiZA8imeZCteshVx0d7gk5quWPgRVQoWgguUZD"

    data = '{ \"messaging_product\": \"whatsapp\", \"to\": \"5511987408516\", \"type\": \"template\", \"template\": { \"name\": \"hello_world\", \"language\": { \"code\": \"en_US\" } } }'


    resp = requests.post(url, headers=headers, data=data)

    #print(resp.status_code)
    #return render_template("post.py")
    return "ok"

@app.route("/usuarios/<nome_user>")
def usuarios(nome_user):
    return render_template("usuarios.html", user_name=nome_user)

if __name__ == "__main__":
    app.run(debug=True)


