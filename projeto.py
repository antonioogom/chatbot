from asyncore import loop
from flask import Flask, request
import requests, mysql.connector
from requests.structures import CaseInsensitiveDict

app = Flask(__name__)

#Páginas ------------------------------------------------------------

@app.route('/webhook2', methods = ['POST'])
def webhook2():
    objConexao = conectaBanco()
    
    dicionario = request.get_json()
    #insertUpdateDeleteBanco(objConexao, "INSERT INTO LOG (RETORNO, ETAPA) VALUES ('APENAS LOG WEBHOOK2', '1')")
    teste = insertUpdateDeleteBanco(objConexao, 'INSERT INTO LOG (RETORNO, ETAPA) VALUES ("' + str(dicionario) + '", "1")')

    desconectaBanco(objConexao)

    return teste

@app.route('/webhook3', methods = ['POST'])
def webhook3():
    sucesso = "nao"
    numQtdeVezes = 10
    con = mysql.connector.connect(host='botuni9.c3cupjqiyqbn.sa-east-1.rds.amazonaws.com', database='ChatBot', user='admin', password='7pPdu#GSX.2sYG')

    if con.is_connected():
        cursor = con.cursor()
        for i in range(numQtdeVezes):
            cursor.execute("INSERT INTO LOG (RETORNO, ETAPA) VALUES ('Loop de testes: " + str(i) + "', '1')")
            con.commit()

        cursor.execute("INSERT INTO LOG (RETORNO, ETAPA) VALUES ('-----------------', '1')")

        cursor.close()
        con.close()

        for i in range(numQtdeVezes):
            insertUpdateDeleteBanco(objConexao, "INSERT INTO LOG (RETORNO, ETAPA) VALUES ('Loop de testes: " + str(i) + "', '1')")

        sucesso = "sim"

    return sucesso

@app.route('/webhook', methods = ['POST'])
def webhook():
    objConexao = conectaBanco()
    dicionario = request.get_json()

    #Coleta dados da mensagem
    strMensagem  = str(dicionario['message']['text'])
    strNome      = str(dicionario['message']['from']['first_name'])
    strChatId    = str(dicionario['message']['from']['id'])

    #Verifica se é a primeira mensagem
    bPrimeiraMensagem = True
    tabFluxoAtual     = retornaFluxoAtual(objConexao, strChatId)

    if len(tabFluxoAtual) > 0:
        bPrimeiraMensagem = False
        strFluxoAtual     = str(tabFluxoAtual[0][0])
        strSequenciaAtual = str(tabFluxoAtual[0][1])

    #Verifica se está cadastrado
    #bExisteCadastro = verificaCadastro(strChatId)

    if bPrimeiraMensagem:
        entraFluxoConversa(objConexao, strChatId, "1")
        strFluxoAtual     = 1
        strSequenciaAtual = 1

        #Guarda a mensagem no BD
        salvaMensagem(objConexao, strChatId, strMensagem, strNome)
        insertUpdateDeleteBanco(objConexao, "INSERT INTO LOG (RETORNO, ETAPA) VALUES ('Guardou mensagem no banco de dados', '1')")

    else:
        #Guarda a mensagem no BD
        salvaMensagem(objConexao, strChatId, strMensagem, strNome)
        insertUpdateDeleteBanco(objConexao, "INSERT INTO LOG (RETORNO, ETAPA) VALUES ('Guardou mensagem no banco de dados', '1')")

        #Verifica resposta recebida
        #Traz todas as respostas aceitas daquela sequencia/fluxo atual
        tabRespostas = selectBanco(objConexao, "SELECT RESPACEITA, IDFLUXOREDIREC FROM RESPOSTAFLUXO WHERE IDFLUXO = '" + strFluxoAtual + "' AND NUMSEQ = '" + strSequenciaAtual + "';")
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
            continuaFluxo(objConexao, strChatId)
        elif len(tabRespostas) == 0:
            entraFluxoConversa(objConexao, strChatId, "1")
        else:
            enviaMsg(strChatId, 'Nao entendi sua resposta, por favor responda corretamente: ')

        #IDENTIFICAR QUANDO ACABAR O FLUXO
        #MELHORAR A FUNÇÃO entraFluxoConversa PARA RESPONDER
        #TALVEZ UNIFICAR A FUNÇÃO CONTINUA COM A ENTRA
        #TA DEMORANDO 2 SEGUNDOS PRA RESPONDER, MELHORAR ISSO

    desconectaBanco(objConexao)

    return "OK"

#Funções de fluxo ---------------------------------------------------

def verificaCadastro(objConexao, strChatId):
    bExisteCadastro = False
    
    tabBancoDados = selectBanco(objConexao, "SELECT * FROM AGENDAMENTOS WHERE IDCTT = '" + strChatId + "';")

    if len(tabBancoDados) > 0:
        bExisteCadastro = True
    
    return bExisteCadastro

def salvaMensagem(objConexao, strChatId, strMensagem, strNomeCtt):
    insertUpdateDeleteBanco(objConexao, "INSERT INTO MENSAGENS_RECEBIDAS (IDCTT, MENSAGEM, NOMECTT) VALUES ('" + strChatId + "', '" + strMensagem + "', '" + strNomeCtt + "');")

def entraFluxoConversa(objConexao, strChatId, strIDFluxo):
    #registrar na tabela contatos o fluxo
    insertUpdateDeleteBanco(objConexao, "DELETE FROM CONTATOS WHERE IDCTT = '" + strChatId + "';")
    insertUpdateDeleteBanco(objConexao, "INSERT INTO CONTATOS (IDCTT, IDFLUXOATUAL, IDNUMSEQATUAL) VALUES ('" + strChatId + "', " + strIDFluxo + ", 1);")
    tabBancoDados = selectBanco(objConexao, "SELECT MENSAGEM FROM FLUXOSMSG WHERE IDFLUXO = '" + strIDFluxo + "' AND NUMSEQ = '1';")

    enviaMsg(strChatId, str(tabBancoDados[0][0]))

    return "ok"

def continuaFluxo(objConexao, strChatId):
    #Verifica o fluxo atual
    tabBancoDados = retornaFluxoAtual(objConexao, strChatId)
    strIDFluxo = str(tabBancoDados[0][0])
    strNumSeq  = str(int(tabBancoDados[0][1]) + 1)

    #Busca a mensagem da sequencia atual
    tabBancoDadosFluxo = selectBanco(objConexao, "SELECT MENSAGEM FROM FLUXOSMSG WHERE IDFLUXO = '" + strIDFluxo + "' AND NUMSEQ = '" + strNumSeq +  "';")

    if len(tabBancoDadosFluxo) > 0:
        #atualiza para a proxima mensagem
        insertUpdateDeleteBanco(objConexao, "UPDATE CONTATOS SET IDNUMSEQATUAL = '" + strNumSeq + "' WHERE IDCTT = '" + strChatId + "'")
        enviaMsg(strChatId, str(tabBancoDadosFluxo[0][0]))
    else:
        entraFluxoConversa(objConexao, strChatId, "1")
        
    return "ok"

def retornaFluxoAtual(objConexao, strChatId):
    tabBancoDados = selectBanco(objConexao, "SELECT IDFLUXOATUAL, IDNUMSEQATUAL FROM CONTATOS WHERE IDCTT = '" + strChatId + "';")

    return tabBancoDados

def enviaMsg(strChatId, strMensagem):

    url = "https://api.telegram.org/bot5751250760:AAG6Fs7zjgKKG8u9S_1BkO53Tn6z5u5C4XI/sendMessage"

    headers = CaseInsensitiveDict()
    headers["Content-Type"] = "application/json"
    data = '{"chat_id":"' + strChatId + '","text":"' + strMensagem + '"}'

    requests.post(url, headers=headers, data=data)

    return "ok"

#Funções de Banco de Dados ------------------------------------------

def conectaBanco():
    objConexao = mysql.connector.connect(host='botuni9.c3cupjqiyqbn.sa-east-1.rds.amazonaws.com', database='ChatBot', user='admin', password='7pPdu#GSX.2sYG')

    return objConexao

def desconectaBanco(objConexao):
    if objConexao.is_connected():
            objConexao.close()
    
    return "Ok"

def selectBanco(objConexao, strQuery):
    #con = mysql.connector.connect(host='botuni9.c3cupjqiyqbn.sa-east-1.rds.amazonaws.com', database='ChatBot', user='admin', password='7pPdu#GSX.2sYG')
    con = objConexao

    if con.is_connected():
        cursor = con.cursor()
        cursor.execute(strQuery)
        resultado = cursor.fetchall()

        cursor.close()
        #con.close()

        return resultado

def insertUpdateDeleteBanco(objConexao, strQuery):
    #con = mysql.connector.connect(host='botuni9.c3cupjqiyqbn.sa-east-1.rds.amazonaws.com', database='ChatBot', user='admin', password='7pPdu#GSX.2sYG')
    con = objConexao
    ok = 'nao'

    if con.is_connected():
        cursor = con.cursor()
        cursor.execute(strQuery)
        con.commit()

        cursor.close()
        #con.close()

        ok = 'ss'

        
    return ok


if __name__ == "__main__":
    app.run(debug=True)