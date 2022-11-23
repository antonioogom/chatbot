import mysql.connector


objConexao = mysql.connector.connect(host='botuni9.c3cupjqiyqbn.sa-east-1.rds.amazonaws.com', database='ChatBot', user='admin', password='7pPdu#GSX.2sYG')

cursor = objConexao.cursor()
cursor.execute("INSERT INTO LOG (RETORNO, ETAPA) VALUES ('Ocorreu um erro na função EnviaMsg', 'Erro');")
objConexao.commit()

cursor.close()