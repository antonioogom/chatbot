from flask import Flask, render_template, request, jsonify
import requests, mysql.connector
from requests.structures import CaseInsensitiveDict

app = Flask(__name__)

@app.route('/webhook', methods = ['POST'])
def webhook():
    dicionario = request.get_json()

    #Coleto dados da mensagem
    strUpdateId  = str(dicionario['result'][0]['update_id'])
    strMensagem  = str(dicionario['result'][0]['message']['text'])
    strNome      = str(dicionario['result'][0]['message']['from']['first_name'])
    strChatId    = str(dicionario['result'][0]['message']['from']['id'])

    #Verifica se é a primeira mensagem
    bPrimeiraMensagem = verificaSePrimeiraMensagem(strChatId)

    #Verifica se está cadastrado
    bExisteCadastro = verificaCadastro(strChatId)

    if bPrimeiraMensagem:
        entraFluxoConversa(strChatId, "1")

    #Guarda a mensagem no BD
    salvaMensagem(strChatId, strMensagem, strNome)

    #Verifica resposta recebida
    #funcao que recebe o chat id, ela vai ver a sequencia atual e as respostas aceitas
    #loop nas respostas aceitas, se uma delas for a mensagem recebida, continua o fluxo
    #se nao, envia mensagem que nao entendeu


    continuaFluxo(strChatId)

    return "ok"

#Funções de fluxo

def verificaSePrimeiraMensagem(strChatId):
    bPrimeiraMensagem = True
    tabBancoDados = selectBanco("SELECT * FROM CONTATOS WHERE DATAHORA >= CURRENT_TIMESTAMP()-10000 AND IDCTT = " + str(strChatId) + ";")

    if len(tabBancoDados) > 0:
        bPrimeiraMensagem = False
    
    return bPrimeiraMensagem

def verificaCadastro(strChatId):
    bExisteCadastro = False
    
    tabBancoDados = selectBanco("SELECT * FROM AGENDAMENTOS WHERE IDCTT = '" + strChatId + "';")

    if len(tabBancoDados) > 0:
        bExisteCadastro = True
    
    return bExisteCadastro

def salvaMensagem(strIDCTT, strMensagem, strNomeCtt):
    con = mysql.connector.connect(host='botuni9.c3cupjqiyqbn.sa-east-1.rds.amazonaws.com', database='ChatBot', user='admin', password='7pPdu#GSX.2sYG')

    if con.is_connected():
        cursor = con.cursor()
        cursor.execute("INSERT INTO MENSAGENS_RECEBIDAS (IDCTT, MENSAGEM, NOMECTT) VALUES ('" + strIDCTT + "', '" + strMensagem + "', '" + strNomeCtt + "');")
        con.commit()

        cursor.close()
        con.close()

        return "ok"

def entraFluxoConversa(strIDCTT, strIDFluxo):
    #registrar na tabela contatos o fluxo
    insertUpdateDeleteBanco("DELETE FROM CONTATOS WHERE IDCTT = '" + strIDCTT + "';")
    insertUpdateDeleteBanco("INSERT INTO CONTATOS (IDCTT, IDFLUXOATUAL, IDNUMSEQATUAL) VALUES ('" + strIDCTT + "', " + strIDFluxo + ", 1);")

    return "ok"

def continuaFluxo(strIDCTT):
    #Verifica o fluxo atual
    tabBancoDados      = selectBanco("SELECT IDFLUXOATUAL, IDNUMSEQATUAL FROM CONTATOS WHERE IDCTT = '" + strIDCTT + "';")
    strIDFluxo = str(tabBancoDados[0][0])
    strNumSeq  = str(tabBancoDados[0][1])

    #Busca a mensagem da sequencia atual
    tabBancoDadosFluxo = selectBanco("SELECT MENSAGEM FROM FLUXOSMSG WHERE IDFLUXO = '" + strIDFluxo + "' AND NUMSEQ = '" + strNumSeq +  "';")

    #atualiza para a proxima mensagem
    insertUpdateDeleteBanco("UPDATE CONTATOS SET IDNUMSEQATUAL = '" + str((int(strNumSeq) + 1)) + "' WHERE IDCTT = '" + strIDCTT + "'")
    enviaMsg(strIDCTT, str(tabBancoDadosFluxo[0][0]))


    return "ok"

    

def enviaMsg(strIDCTT, strMensagem):

    url = "https://api.telegram.org/bot5751250760:AAG6Fs7zjgKKG8u9S_1BkO53Tn6z5u5C4XI/sendMessage"

    headers = CaseInsensitiveDict()
    headers["Content-Type"] = "application/json"
    data = '{"chat_id":"' + strIDCTT + '","text":"' + strMensagem + '"}'

    requests.post(url, headers=headers, data=data)

    return "ok"


#Funções de Banco de Dados

def selectBanco(strQuery):
    con = mysql.connector.connect(host='botuni9.c3cupjqiyqbn.sa-east-1.rds.amazonaws.com', database='ChatBot', user='admin', password='7pPdu#GSX.2sYG')

    if con.is_connected():
        cursor = con.cursor()
        cursor.execute(strQuery)
        resultado = cursor.fetchall()

        cursor.close()
        con.close()

        return resultado

def insertUpdateDeleteBanco(strQuery):
    con = mysql.connector.connect(host='botuni9.c3cupjqiyqbn.sa-east-1.rds.amazonaws.com', database='ChatBot', user='admin', password='7pPdu#GSX.2sYG')

    if con.is_connected():
        cursor = con.cursor()
        cursor.execute(strQuery)
        con.commit()

        cursor.close()
        con.close()

        return "ok"


if __name__ == "__main__":
    app.run(debug=True)