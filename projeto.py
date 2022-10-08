from flask import Flask, request
import requests, mysql.connector
from requests.structures import CaseInsensitiveDict

app = Flask(__name__)

@app.route('/webhook2', methods = ['POST'])
def webhook2():
    insertUpdateDeleteBanco("INSERT INTO LOG (OK) VALUES ('OK')")

    return "ok"

@app.route('/webhook', methods = ['POST'])
def webhook():
    dicionario = request.get_json()

    #Coleta dados da mensagem
    strMensagem  = str(dicionario['result'][0]['message']['text'])
    strNome      = str(dicionario['result'][0]['message']['from']['first_name'])
    strChatId    = str(dicionario['result'][0]['message']['from']['id'])

    #Verifica se é a primeira mensagem
    bPrimeiraMensagem = True
    tabFluxoAtual     = retornaFluxoAtual(strChatId)

    if len(tabFluxoAtual) > 0:
        bPrimeiraMensagem = False
        strFluxoAtual     = str(tabFluxoAtual[0][0])
        strSequenciaAtual = str(tabFluxoAtual[0][1])

    #Verifica se está cadastrado
    #bExisteCadastro = verificaCadastro(strChatId)

    if bPrimeiraMensagem:
        entraFluxoConversa(strChatId, "1")
        strFluxoAtual     = 1
        strSequenciaAtual = 1

        #Guarda a mensagem no BD
        salvaMensagem(strChatId, strMensagem, strNome)

    else:
        #Guarda a mensagem no BD
        salvaMensagem(strChatId, strMensagem, strNome)

        #Verifica resposta recebida
        #Traz todas as respostas aceitas daquela sequencia/fluxo atual
        tabRespostas = selectBanco("SELECT RESPACEITA, IDFLUXOREDIREC FROM RESPOSTAFLUXO WHERE IDFLUXO = '" + strFluxoAtual + "' AND NUMSEQ = '" + strSequenciaAtual + "';")
        bRespostaAceita = False

        #Loop nas respostas aceitas verificando se ela é igual a resposta recebida
        if len(tabRespostas) > 0:
            for linha in tabRespostas:
                strResposta = linha[0]

                if strResposta == '*':
                    bRespostaAceita = True
                    break

                elif strMensagem.upper() == strResposta.upper():
                    bRespostaAceita = True
                    break


        if bRespostaAceita:
            #Responde e continua o fluxo
            continuaFluxo(strChatId)
        elif len(tabRespostas) == 0:
            entraFluxoConversa(strChatId, "1")
        else:
            enviaMsg(strChatId, 'Nao entendi sua resposta, por favor responda corretamente: ')

        #IDENTIFICAR QUANDO ACABAR O FLUXO
        #MELHORAR A FUNÇÃO entraFluxoConversa PARA RESPONDER
        #TALVEZ UNIFICAR A FUNÇÃO CONTINUA COM A ENTRA
        #TA DEMORANDO 2 SEGUNDOS PRA RESPONDER, MELHORAR ISSO

    return str(strSequenciaAtual)

#Funções de fluxo

def verificaCadastro(strChatId):
    bExisteCadastro = False
    
    tabBancoDados = selectBanco("SELECT * FROM AGENDAMENTOS WHERE IDCTT = '" + strChatId + "';")

    if len(tabBancoDados) > 0:
        bExisteCadastro = True
    
    return bExisteCadastro

def salvaMensagem(strChatId, strMensagem, strNomeCtt):
    con = mysql.connector.connect(host='botuni9.c3cupjqiyqbn.sa-east-1.rds.amazonaws.com', database='ChatBot', user='admin', password='7pPdu#GSX.2sYG')

    if con.is_connected():
        cursor = con.cursor()
        cursor.execute("INSERT INTO MENSAGENS_RECEBIDAS (IDCTT, MENSAGEM, NOMECTT) VALUES ('" + strChatId + "', '" + strMensagem + "', '" + strNomeCtt + "');")
        con.commit()

        cursor.close()
        con.close()

        return "ok"

def entraFluxoConversa(strChatId, strIDFluxo):
    #registrar na tabela contatos o fluxo
    insertUpdateDeleteBanco("DELETE FROM CONTATOS WHERE IDCTT = '" + strChatId + "';")
    insertUpdateDeleteBanco("INSERT INTO CONTATOS (IDCTT, IDFLUXOATUAL, IDNUMSEQATUAL) VALUES ('" + strChatId + "', " + strIDFluxo + ", 1);")
    tabBancoDados = selectBanco("SELECT MENSAGEM FROM FLUXOSMSG WHERE IDFLUXO = '" + strIDFluxo + "' AND NUMSEQ = '1';")

    enviaMsg(strChatId, str(tabBancoDados[0][0]))

    return "ok"

def continuaFluxo(strChatId):
    #Verifica o fluxo atual
    tabBancoDados = retornaFluxoAtual(strChatId)
    strIDFluxo = str(tabBancoDados[0][0])
    strNumSeq  = str(int(tabBancoDados[0][1]) + 1)

    #Busca a mensagem da sequencia atual
    tabBancoDadosFluxo = selectBanco("SELECT MENSAGEM FROM FLUXOSMSG WHERE IDFLUXO = '" + strIDFluxo + "' AND NUMSEQ = '" + strNumSeq +  "';")

    if len(tabBancoDadosFluxo) > 0:
        #atualiza para a proxima mensagem
        insertUpdateDeleteBanco("UPDATE CONTATOS SET IDNUMSEQATUAL = '" + strNumSeq + "' WHERE IDCTT = '" + strChatId + "'")
        enviaMsg(strChatId, str(tabBancoDadosFluxo[0][0]))
    else:
        entraFluxoConversa(strChatId, "1")
        
    return "ok"

def retornaFluxoAtual(strChatId):
    tabBancoDados = selectBanco("SELECT IDFLUXOATUAL, IDNUMSEQATUAL FROM CONTATOS WHERE IDCTT = '" + strChatId + "';")

    return tabBancoDados

def enviaMsg(strChatId, strMensagem):

    url = "https://api.telegram.org/bot5751250760:AAG6Fs7zjgKKG8u9S_1BkO53Tn6z5u5C4XI/sendMessage"

    headers = CaseInsensitiveDict()
    headers["Content-Type"] = "application/json"
    data = '{"chat_id":"' + strChatId + '","text":"' + strMensagem + '"}'

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