import mysql.connector

con = mysql.connector.connect(host='botuni9.c3cupjqiyqbn.sa-east-1.rds.amazonaws.com', database='ChatBot', user='admin', password='7pPdu#GSX.2sYG')

if con.is_connected():
    db_info = con.get_server_info()
    print("Conectado. Versão do BD: ", db_info)
    cursor = con.cursor()
    cursor.execute("INSERT INTO TESTE VALUES (2, 'A', 'A');")

    con.commit()
    
    linha = cursor.fetchone()
    print(linha)

if con.is_connected():
    cursor.close()
    con.close()
    print("fechou a conex.")