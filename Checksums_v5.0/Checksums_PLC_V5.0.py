#BIBLIOTECAS
#--------------
import snap7 #interface com PLC
from datetime import date #ler data
import shutil #copiar arquivos
import glob
import os, csv, time, pathlib, sys
import dbfread
from dbfread import DBF
import sqlite3
import PySimpleGUI as sg
#----------------

#VARIAVEIS GLOBAIS
#------------------
plc = snap7.client.Client()
diretorio_origem = str(pathlib.Path(__file__).parent.absolute())
diretorio_origem = str(diretorio_origem+"/")
argc = len(sys.argv)
persistent_db=sqlite3.connect(str(diretorio_origem+'Checksums_database.db'))
volatile_db=sqlite3.connect(':memory:')
#------------------------

#FUNCOES
#---------------------------------------------------------------------
#CONEXAO COM PLC
#-------------------------------------------------------------------
def Conectar_com_PLC(IP_do_PLC,Numero_do_Rack,Numero_do_slot):
    Status_de_conexao=0
    tentativas=1

    while not Status_de_conexao:
        try:
            plc.connect(IP_do_PLC,Numero_do_Rack,Numero_do_slot)
            Status_de_conexao = (plc.get_connected())
            if Status_de_conexao == True:
                print('Conexão em '+IP_do_PLC+' estabelecida com sucesso\n')
        except:
            print (str('Tentativa '+str(tentativas)+' de conexão com '+IP_do_PLC+' falhou\n'))
            if tentativas==10:
                raise Exception("Limite de tentativas de conexão excedido")
            tentativas=tentativas+1
            plc.disconnect()
            time.sleep(2)            
#---------------------------------------------------------------------

#-------------------------------------------------------------------
#EXECUTA QUERY EM BANCO DE DADOS E GRAVA MODIFICAÇÕES
#-----------------------------------------------------------------------------------------
def Query_database(sql_query, sql_database):

    result=sql_database.cursor().execute(sql_query).fetchall()    
    sql_database.commit()
    return result
#-------------------------------------------------------------------
#-----------------------------------------------------------------------------------------

#-------------------------------------------------------------------
#LISTA CHECKSUMS DE OBTIDOS NA ÚLTIMA VARREDURA
#-----------------------------------------------------------------------------------------
def list_checksums_from_last_scan(plc_id):
    print("Listando checksums dos blocos obtidos na ÚLTIMA VARREDURA\n")
    Query_database("""CREATE TABLE IF NOT EXISTS checksums (plc_id,block,checksum);""",persistent_db)
    checksum_list=Query_database("""SELECT block,checksum 
    FROM checksums 
    WHERE plc_id = '"""+str(plc_id)+"""';""",persistent_db)
    return checksum_list

#LER CHECKSUM DE BLOCO ESPECÍFICO
#--------------------------------------------------------------------
def Checksum_Bloco(Tipo_do_bloco,numero_do_bloco):
    Checksum = plc.get_block_info(Tipo_do_bloco,numero_do_bloco).CheckSum
    Checksum=decimal_little_to_big_endian(Checksum)
    return Checksum
#--------------------------------------------------------------------    
#--------------------------------------------------------------------

#CONVERTE DECIMAL OBTIDO POR LITTLE ENDIAN PARA DECIMAL OBTIDO POR BIG ENDIAN
#--------------------------------------------------------------------
def decimal_little_to_big_endian(base_10):    
    base_256=[]
    while base_10>=256:   
        base_256.append(int(base_10%256))
        base_10=int(base_10/256)
    base_256.append(int(base_10%256))
    
    base_10=0
    for i in range (len(base_256)):
        base_10=base_256[i]*pow(256,len(base_256)-1-i)+base_10
    
    return str(base_10)
#--------------------------------------------------------------------
#--------------------------------------------------------------------    

#-------------------------------------------------------------------
#LISTA CHECKSUMS DE TODOS OS BLOCOS ONLINE
#-----------------------------------------------------------------------------------------
def list_online_blocks_checksum():
    print("Listando checksums dos blocos no CLP ONLINE\n")
    checksum_list=[]
    tipos = ['OB','FB','FC']
    for tipo in tipos:
        try:
            indices_do_tipo = plc.list_blocks_of_type(str(tipo),1000)
        except:
            indices_do_tipo=[]
        indice_anterior=0
        for indice in indices_do_tipo:
            if indice>=indice_anterior:
                checksum_list.append((str(str(tipo)+" "+str(indice)),int(Checksum_Bloco(str(tipo),indice))))
                indice_anterior=indice
    return checksum_list
#-----------------------------------------------------------------------------------------
#---------------------------------------------------------------------

#ESCREVE NO BANCO DE DADOS OS CHECKSUMS DE ARQUIVO DE BACKUP OFFLINE CRIADO EM S7 MANAGER
#-------------------------------------------------------------------
def list_offline_backup_checksums(diretorio_plc,plc_id):
    print("Listando checksums dos blocos no BACKUP OFFLINE\n")
    endereco_DBF = str(diretorio_plc+'S7_proj/'+plc_id+'/ombstx/offline/00000001/SUBBLK.dbf') 
    table=DBF(endereco_DBF,raw=True)
    checksum_list=[]
    tipos = {8:'OB',12:'FC',14:'FB'}    
    for record in table:
        if int(record['SUBBLKTYP']) in tipos:
            tipo=int(record['SUBBLKTYP'])
            tipo=tipos[tipo]
            indice=int(record['BLKNUMBER'])
            Checksum_Bloco=int(record['CHECKSUM'])         
            checksum_list.append((str(str(tipo)+" "+str(indice)),Checksum_Bloco))

    return checksum_list
#-----------------------------------------------------------------------------------------
#---------------------------------------------------------------------

#COMPARA CHECKSUMS ANTIGOS COM NOVOS E GERA RELATORIO DE DIFERENÇAS
#-------------------------------------------------------------------
def compara_checksums_novos_antigos(plc_id,diretorio_plc,checksums_antigos,checksums_novos,current_time_stamp):          
    print("Comparando checksums de : "+plc_id+" \n")
    diferencas=str(diretorio_plc+"changelog.txt")

    inexistente=[]    
    modificado=[]
    adicionado=[]
    for antigo in checksums_antigos:
        if antigo not in checksums_novos:
            inexistente.append(antigo[0])
    for novo in checksums_novos:
        if novo not in checksums_antigos:
            adicionado.append(novo[0])    
    for bloco in adicionado:
        if bloco in inexistente:
            modificado.append(bloco)
    
    for bloco in modificado:
        adicionado.remove(bloco)
        inexistente.remove(bloco)
        
    with open(diferencas, "a") as outFile:
        outFile.write("\n\n")
        outFile.write(current_time_stamp)
        if modificado:
            outFile.write("\nOS SEGUINTES BLOCOS FORAM MODIFICADOS DESDE A ÚLTIMA COMPARAÇÃO:\n")
            for bloco in modificado:
                outFile.write(str(bloco+", "))
        if inexistente:
            outFile.write("\nOS SEGUINTES BLOCOS FORAM REMOVIDOS DESDE A ÚLTIMA COMPARAÇÃO:\n")
            for bloco in inexistente:
                outFile.write(str(bloco+", "))
        if adicionado:
            outFile.write("\nOS SEGUINTES BLOCOS FORAM ADICIONADOS DESDE A ÚLTIMA COMPARAÇÃO:\n")
            for bloco in adicionado:
                outFile.write(str(bloco+", "))                  
        if not modificado and not inexistente and not adicionado:
            outFile.write("\nNÃO FORAM DETECTADAS MUDANÇAS DESDE A ÚLTIMA COMPARAÇÃO\n")
            status = False
        else:
            print("Foram detectadas mudanças no codigo fonte do PLC")
            input("Pressione ENTER para continuar a execução")
            status = True
        outFile.close()       
        
    print("Gerando changelog em: \n"+diferencas+"\n")
    return (current_time_stamp,status)   
#-----------------------------------------------------------------------------------------
#---------------------------------------------------------------------

#COMPARA CHECKSUMS ONLINE COM BACKUP OFFLINE E GERA RELATORIO DE DIFERENÇAS
#-------------------------------------------------------------------
def compara_checksums_online_offline(plc_id,diretorio_plc,checksums_online,checksums_offline):          
    print("Comparando checksums de : "+plc_id+" \n")
    diferencas=str(diretorio_plc+"changelog.txt")
                  
    inexistente=[]
    modificado=[]
    adicionado=[]    
    for online in checksums_online:
        if online not in checksums_offline:
            adicionado.append(online[0])
    for offline in checksums_offline:
        if offline not in checksums_online:
            inexistente.append(offline[0])
    for bloco in adicionado:
        if bloco in inexistente:
            modificado.append(bloco)
    for bloco in modificado:
        adicionado.remove(bloco)
        inexistente.remove(bloco)

    
    with open(diferencas, "a") as outFile:
        if modificado:
            outFile.write("\nOS SEGUINTES BLOCOS ESTÃO DIFERENTES DO BACKUP OFFLINE:\n")
            for bloco in modificado:
                outFile.write(str(bloco+", "))
        if inexistente:
            outFile.write("\nOS SEGUINTES BLOCOS EXISTEM APENAS NO BACKUP OFFLINE:\n")
            for bloco in inexistente:
                outFile.write(str(bloco+", "))
        if adicionado:
            outFile.write("\nOS SEGUINTES BLOCOS NÃO EXISTEM NO BACKUP OFFLINE:\n")
            for bloco in adicionado:
                outFile.write(str(bloco+", "))                  
        if not modificado and not inexistente and not adicionado:
            outFile.write("\nBACKUP OFFLINE IDENTICO AO ONLINE\n")
            status = False
        else:
            status = True
        outFile.close()
        return status
#-----------------------------------------------------------------------------------------
#---------------------------------------------------------------------

#-------------------------------------------------------------------
#ATUALIZA NO DB CHECKSUMS DE TODOS OS BLOCOS ONLINE
#-----------------------------------------------------------------------------------------
def write_online_blocks_checksum_to_db(plc_id,sql_placeholders):
    print("Atualizando checksums online no banco de dados\n")
    try:
        Query_database("""CREATE TABLE IF NOT EXISTS checksums (plc_id,block,checksum);""",persistent_db)
        Query_database(str("""DELETE FROM checksums WHERE plc_id = '"""+str(plc_id)+"""';"""),persistent_db)
        sql_query="INSERT INTO checksums VALUES ('"+str(plc_id)+"',?,?);"
        persistent_db.cursor().executemany(sql_query,(sql_placeholders))    
        persistent_db.commit()
    except:
        print("Ocorreu um erro ao atualizar checksums de "+str(plc_id)+" no banco de dados")
        
#-----------------------------------------------------------------------------------------
#---------------------------------------------------------------------

#-------------------------------------------------------------------
#ATUALIZA STATUS RESUMIDO NO DB
#-----------------------------------------------------------------------------------------
def update_status_to_db(status_online,status_offline,plc_id):
    if not Query_database(str("""SELECT * FROM status WHERE plc_id = '"""+str(plc_id)+"""';"""),persistent_db):
        Query_database("INSERT INTO status (plc_id) VALUES ('"+str(plc_id)+"');",persistent_db)
    Query_database("UPDATE status SET last_scan = '"+str(status_online[0])+"' WHERE plc_id = '"+str(plc_id)+"';",persistent_db)
    
    if status_online[1]:
        Query_database("UPDATE status SET last_change_online = '"+str(status_online[0])+"' WHERE plc_id = '"+str(plc_id)+"';",persistent_db)

    if not status_offline:
        Query_database("UPDATE status SET last_time_online_eq_offline = '"+str(status_online[0])+"' WHERE plc_id = '"+str(plc_id)+"';",persistent_db)
    
#-------------------------------------------------------------------
#-----------------------------------------------------------------------------------------


#Engine
#-----------------------------------------------------------------------------------------
def Engine(Nome_PLC,IP,Rack,Slot):
    print("INICIANDO DETECTOR DE MODIFICACOES DE PROGRAMA DE PLC\n")
    Conectar_com_PLC(IP,Rack,Slot)

    diretorio_plc = str(diretorio_origem + Nome_PLC + "/")
    if not os.path.exists(diretorio_plc):
        os.mkdir(diretorio_plc)
    if not os.path.exists(str(diretorio_plc+"S7_proj/")):
        os.mkdir(str(diretorio_plc+"S7_proj/"))

    Tempo = time.localtime()
    time_stamp = str(str(Tempo[2])+"_"+str(Tempo[1])+"_"+str(Tempo[0])+"__"+str(Tempo[3])+"h"+str(Tempo[4])+"m"+str(Tempo[5])+"s")

    Query_database("""CREATE TABLE IF NOT EXISTS status (plc_id,last_scan,last_change_online,last_time_online_eq_offline);""",persistent_db)

    Checksums_offline=list_offline_backup_checksums(diretorio_plc,Nome_PLC)
    Checksums_antigos=list_checksums_from_last_scan(Nome_PLC)
    Checksums_novos=list_online_blocks_checksum()

    
    Status_online = compara_checksums_novos_antigos(Nome_PLC,diretorio_plc,Checksums_antigos,Checksums_novos,time_stamp)
    
    try:
        Status_offline = compara_checksums_online_offline(Nome_PLC,diretorio_plc,Checksums_novos,Checksums_offline)
    except:
        print("Não foi possível realizar comparação Online/Offline")
        Status_offline=True
    
    write_online_blocks_checksum_to_db(Nome_PLC,Checksums_novos)
    
    update_status_to_db(Status_online,Status_offline,Nome_PLC)
    
    plc.disconnect()
#-----------------------------------------------------------------------------------------

#PRINCIPAL
#-----------------------------------------------------------------------------------------
def main():
    Dados_de_entrada = csv.DictReader(open(str(diretorio_origem+"dados.csv")))
    for row in Dados_de_entrada:
        try:
            Engine(row['Nome'],row['IP'],int(row['Rack']),int(row['Slot']))                
        except:
            print(str("Não foi possível comparar "+row['Nome']))
    input("Pressione ENTER para concluir execução")
    print("Execução concluída\n")
#-----------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------

# INTERFACE GRÁFICA
#-----------------------------------------------------------------------------------------
sg.theme('DarkAmber')   # Add a touch of color
# All the stuff inside your window.
table_1=Query_database("SELECT * FROM status",persistent_db)
headings_1=("Identificação","Última Varredura","Última modificação detectada","Última vez que online=offline")
layout = [  [sg.Table(values=table_1,headings=headings_1,justification='center',key="-table_1-")],
            [sg.Button('Atualizar')] ]
# Create the Window
window = sg.Window('DETECTOR DE MODIFICAÇÕES DE CÓDIGO FONTE', layout)
# Event Loop to process "events" and get the "values" of the inputs

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break
    if event == 'Atualizar':
        main()
        window["-table_1-"].update(values=Query_database("SELECT * FROM status",persistent_db))

window.close()
#-----------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------
