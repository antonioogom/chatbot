from flask import Flask, request
import requests, mysql.connector
from requests.structures import CaseInsensitiveDict

app = Flask(__name__)

#Conexao com o banco de dados ---------------------------------------

objConexao = mysql.connector.connect(host='botuni9.c3cupjqiyqbn.sa-east-1.rds.amazonaws.com', database='ChatBot', user='admin', password='7pPdu#GSX.2sYG')

#Páginas ------------------------------------------------------------

@app.route('/webhook', methods = ['POST'])
def webhook():

    try:
        #Transforma a string JSON numa variável tipo dicionadio do Python
        dicionario = request.get_json()

        #Coleta dados da mensagem
        strMensagem  = str(dicionario['message']['text'])
        strNome      = str(dicionario['message']['from']['first_name'])
        strChatId    = str(dicionario['message']['from']['id'])

        #Guarda a mensagem no Banco de dados
        guardaMensagem(strChatId, strMensagem, strNome)

        #Verifica se é a primeira mensagem que o contato envia para o bot
        bPrimeiraMensagem = True
        tabFluxoAtual     = retornaFluxoAtual(strChatId)

        if len(tabFluxoAtual) > 0:        
            bPrimeiraMensagem = False
            strFluxoAtual     = str(tabFluxoAtual[0][0])
            strSequenciaAtual = str(tabFluxoAtual[0][1])

        #Separa os caminhos caso seja a primeira mensagem ou caso o usuario já esteve em uma conversa
        if bPrimeiraMensagem:

            #Verifica se o usuário está cadastrado
            bExisteCadastro = verificaCadastro(strChatId)

            #Separa os caminhos caso, se o usuário estiver cadastrado será enviada uma mensagem, se não estiver será enviado outra
            if bExisteCadastro:
                #Entra no primeiro fluxo de mensagem
                entraFluxoConversa(strChatId, "1")
                strFluxoAtual     = 1
                strSequenciaAtual = 1
            else:
                #Entra no primeiro fluxo de mensagem
                entraFluxoConversa(strChatId, "4")
                strFluxoAtual     = 4
                strSequenciaAtual = 1
            
        else:
            #Se não for a primeira mensagem, irá continua uma conversa
            #Traz todas as respostas aceitas daquela sequencia/fluxo que o usuário está
            tabRespostas = selectBanco(objConexao, "SELECT RESPACEITA, IDFLUXOREDIREC FROM RESPOSTAFLUXO WHERE IDFLUXO = '" + strFluxoAtual + "' AND NUMSEQ = '" + strSequenciaAtual + "';")
            bRespostaAceita = False

            #Loop nas respostas aceitas verificando se ela é igual a resposta recebida
            if len(tabRespostas) > 0:
                for linha in tabRespostas:
                    strResposta          = linha[0]
                    strRedirecionarFluxo = linha[1]

                    if strResposta == '*':
                        bRespostaAceita = True
                        break

                    elif strMensagem.upper() == strResposta.upper():
                        bRespostaAceita = True
                        break

            if bRespostaAceita:
                if strRedirecionarFluxo == None:                
                    #Responde e continua o fluxo
                    if strFluxoAtual == '5' and strSequenciaAtual == '2':
                        insertUpdateDeleteBanco(objConexao, "INSERT INTO CONTATO_LINHA (IDCTT, IDLINHA) VALUES ('" + strChatId + "', '" + strMensagem + "');")

                    if strFluxoAtual == '5' and strSequenciaAtual == '4':
                        insertUpdateDeleteBanco(objConexao, "INSERT INTO CONTATO_AGENDAMENTOS (IDCTT, HORA) VALUES ('" + strChatId + "', '" + strMensagem + "');")
        
                    continuaFluxo(strChatId)
                else:
                    #Redireciona para o fluxo de acordo com o cadastro do banco
                    entraFluxoConversa(strChatId, strRedirecionarFluxo)
                
            elif len(tabRespostas) == 0:
                entraFluxoConversa(strChatId, "1")
            else:
                enviaMsgBotao(strChatId, 'Nao entendi sua resposta, por favor responda corretamente.', '')
    except:
        return "ERROR"

    return "OK"

#Funções de fluxo ---------------------------------------------------

def verificaCadastro(strChatId):
    bExisteCadastro = False
    
    tabBancoDados = selectBanco(objConexao, "SELECT * FROM CONTATO_AGENDAMENTOS WHERE IDCTT = '" + strChatId + "';")

    if len(tabBancoDados) > 0:
        bExisteCadastro = True
    
    return bExisteCadastro

def guardaMensagem(strChatId, strMensagem, strNomeCtt):
    insertUpdateDeleteBanco(objConexao, "INSERT INTO MENSAGENS_RECEBIDAS (IDCTT, MENSAGEM, NOMECTT) VALUES ('" + strChatId + "', '" + strMensagem + "', '" + strNomeCtt + "');")

def entraFluxoConversa(strChatId, strIDFluxo):
    strIDFluxo = str(strIDFluxo)
    #registrar na tabela contatos o fluxo
    insertUpdateDeleteBanco(objConexao, "DELETE FROM CONTATOS WHERE IDCTT = '" + strChatId + "';")
    insertUpdateDeleteBanco(objConexao, "INSERT INTO CONTATOS (IDCTT, IDFLUXOATUAL, IDNUMSEQATUAL) VALUES ('" + strChatId + "', " + str(strIDFluxo) + ", 1);")
    tabBancoDados       = selectBanco(objConexao, "SELECT MENSAGEM   FROM FLUXOSMSG     WHERE IDFLUXO = '" + strIDFluxo + "' AND NUMSEQ = '1';")
    tabBancoDadosBotoes = selectBanco(objConexao, "SELECT RESPACEITA FROM RESPOSTAFLUXO WHERE IDFLUXO = '" + strIDFluxo + "' AND NUMSEQ = '1' AND BOTAO = 'S';")

    enviaMsgBotao(strChatId, str(tabBancoDados[0][0]), tabBancoDadosBotoes)

    return "ok"

def continuaFluxo(strChatId):
    #Verifica o fluxo atual
    tabBancoDados = retornaFluxoAtual(strChatId)
    strIDFluxo = str(tabBancoDados[0][0])
    strNumSeq  = str(int(tabBancoDados[0][1]) + 1)

    #Busca a mensagem da sequencia atual
    tabBancoDadosFluxo = selectBanco(objConexao,  "SELECT MENSAGEM   FROM FLUXOSMSG     WHERE IDFLUXO = '" + strIDFluxo + "' AND NUMSEQ = '" + strNumSeq +  "';")
    tabBancoDadosBotoes = selectBanco(objConexao, "SELECT RESPACEITA FROM RESPOSTAFLUXO WHERE IDFLUXO = '" + strIDFluxo + "' AND NUMSEQ = '" + strNumSeq +  "' AND BOTAO = 'S';")

    if len(tabBancoDadosFluxo) > 0:
        #atualiza para a proxima mensagem
        insertUpdateDeleteBanco(objConexao, "UPDATE CONTATOS SET IDNUMSEQATUAL = '" + strNumSeq + "' WHERE IDCTT = '" + strChatId + "'")
        #enviaMsg(strChatId, str(tabBancoDadosFluxo[0][0]))
        enviaMsgBotao(strChatId, str(tabBancoDadosFluxo[0][0]), tabBancoDadosBotoes)
    else:
        entraFluxoConversa(strChatId, "1")
        
    return "ok"

def retornaFluxoAtual(strChatId):
    tabBancoDados = selectBanco(objConexao, "SELECT IDFLUXOATUAL, IDNUMSEQATUAL FROM CONTATOS WHERE IDCTT = '" + strChatId + "';")

    return tabBancoDados

def enviaMsg(strChatId, strMensagem):

    try:
        url = "https://api.telegram.org/bot5751250760:AAG6Fs7zjgKKG8u9S_1BkO53Tn6z5u5C4XI/sendMessage"

        headers = CaseInsensitiveDict()
        headers["Content-Type"] = "application/json"
        data = '{"chat_id":"' + strChatId + '","text":"' + strMensagem + '"}'
        data = data.encode("utf-8")

        resposta = requests.post(url, headers=headers, data=data)
        #insertUpdateDeleteBanco(objConexao, "INSERT INTO LOG (RETORNO, ETAPA) VALUES ('" + str(resposta) + "', 'Sucesso');")
    except:
        insertUpdateDeleteBanco(objConexao, "INSERT INTO LOG (RETORNO, ETAPA) VALUES ('Ocorreu um erro', 'Erro');")

    return "ok"

def enviaMsgBotao(strChatId, strMensagem, tabBancoDados):
    try:
        url = "https://api.telegram.org/bot5751250760:AAG6Fs7zjgKKG8u9S_1BkO53Tn6z5u5C4XI/sendMessage"

        headers = CaseInsensitiveDict()
        headers["Content-Type"] = "application/json"

        strBotoes = ''
        if len(tabBancoDados) == 0:
            data = '{"chat_id":"' + strChatId + '","text":"' + strMensagem + '", "reply_markup":{"remove_keyboard":true}}'
        else:

            data = '{"chat_id":"' + strChatId + '","text":"' + strMensagem + '","reply_markup":{"keyboard":['

            for linha in tabBancoDados:
                strBotoes = strBotoes + '[{"text":"'+ linha[0] +'"}]' + ","

            data = data + strBotoes
            data = data + ']}}'

            data = data.replace(",]}}", "]}}")

        data = data.encode("utf-8")

        resposta = requests.post(url, headers=headers, data=data)
    except:
        insertUpdateDeleteBanco(objConexao, "INSERT INTO LOG (RETORNO, ETAPA) VALUES ('Ocorreu um erro', 'Erro');")

    return "ok"

#Funções de Banco de Dados ------------------------------------------

def selectBanco(objConexao, strQuery):
    con = objConexao

    if con.is_connected():
        cursor = con.cursor()
        cursor.execute(strQuery)
        resultado = cursor.fetchall()

        cursor.close()

        return resultado

def insertUpdateDeleteBanco(objConexao, strQuery):
    con = objConexao

    if con.is_connected():
        cursor = con.cursor()
        cursor.execute(strQuery)
        con.commit()

        cursor.close()
        
    return "ok"

def guardaStatusMetro():
    request = requests.get("https://www.diretodostrens.com.br/api/status")

    conteudo = request.json()

    for linha in conteudo:

        #insertUpdateDeleteBanco(objConexao, "INSERT INTO STATUS_METRO (CODIGO, SITUACAO) VALUES ('" + str(linha['codigo']) +  "', '" + str(linha['situacao']) +  "');")
        insertUpdateDeleteBanco(objConexao, "UPDATE STATUS_METRO SET SITUACAO = '" + str(linha['situacao']) +  "', DTATUALIZACAO = CURRENT_TIMESTAMP WHERE CODIGO = '" + str(linha['codigo']) +  "';")

#if objConexao.is_connected():
    #objConexao.close()

if __name__ == "__main__":
    app.run(debug=True)