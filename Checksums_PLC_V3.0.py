#BIBLIOTECAS
#--------------
import snap7 #interface com PLC
from datetime import date #ler data
import shutil #copiar arquivos
import glob
import os, csv, time, pathlib, sys
#----------------

#VARIAVEIS GLOBAIS
#------------------
plc = snap7.client.Client()
Tempo = time.localtime()
time_stamp = str(str(Tempo[2])+"_"+str(Tempo[1])+"_"+str(Tempo[0])+"__"+str(Tempo[3])+"h"+str(Tempo[4])+"m"+str(Tempo[5])+"s")
diretorio_origem = str(pathlib.Path(__file__).parent.absolute())
diretorio_origem = str(diretorio_origem+"/")
argc = len(sys.argv)
#------------------------

#FUNCOES
#---------------------------------------------------------------------
#CONEXAO COM PLC
#-------------------------------------------------------------------
def Conectar_com_PLC(IP_do_PLC,Numero_do_Rack,Numero_do_slot):
    plc.connect(IP_do_PLC,Numero_do_Rack,Numero_do_slot)
    Status_de_conexao = (plc.get_connected())
    if Status_de_conexao == True:
        print('Conexão em '+IP_do_PLC+' estabelecida com sucesso\n')
    else:
        print ('Há problemas na conexão com o PLC\n')
        input()
#---------------------------------------------------------------------

#LER CHECKSUM DE BLOCO ESPECÍFICO
#--------------------------------------------------------------------
def Checksum_Bloco(Tipo_do_bloco,numero_do_bloco):
    Checksum = plc.get_block_info(Tipo_do_bloco,numero_do_bloco)
    for item in str(Checksum).split("\n"):
        if "Checksum" in item:
            Checksum = item.strip()
    for item in str(Checksum).split("Checksum: "):
        valor_do_checksum = item.strip()
    Checksum = str(valor_do_checksum)
    return Checksum
#--------------------------------------------------------------------    

#COMPARA .CSVs E GERA RELATORIO DE DIFERENÇAS
#-------------------------------------------------------------------
def compara_csv(entrada_1,entrada_2,diferencas):
    print("Comparando: \n"+entrada_1+" com \n"+entrada_2)
    flag_null_lines=0
    with open(entrada_1, 'r') as t1, open(entrada_2, 'r') as t2:
        fileone = t1.readlines()
        filetwo = t2.readlines()
    with open(diferencas, "a") as outFile:
        outFile.write("\n\n")
        outFile.write(str(time_stamp+"\n"))
        outFile.write("OS SEGUINTES BLOCOS FORAM MODIFICADOS DESDE A ÚLTIMA COMPARAÇÃO:\n")
        for line in filetwo:
            if line not in fileone:
                line_list=line.split(",")
                line =str(line_list[0]+" "+line_list[1]+", ")
                if line != "":
                    flag_null_lines=1
                outFile.write(line)
    if flag_null_lines==1:
        print("Foram detectadas mudanças no codigo fonte do PLC")
        input("Pressione ENTER para continuar a execução")
    print("Gerado changelog em: \n"+diferencas+"\n")
#-------------------------------------------------------------------

#GERA .CSV COM DADOS DE CHECKSUM DE TODOS OS BLOCOS
#-----------------------------------------------------------------------------------------
def all_blocks_checksum_to_csv(diretorio_do_plc,IP):
    print("Gerando banco de dados de checksums dos blocos em "+IP+"\n")
    Output = open(str(diretorio_do_plc+"Historico/new.csv"), "w")
    Output.write("Tipo,Indice,Checksums"+"\n")
    tipos = ['OB','FB','FC']
    for tipo in tipos:
        indices_do_tipo = plc.list_blocks_of_type(str(tipo),1000)
        for item in indices_do_tipo:
            if item != 0:
                Output.write(str(tipo)+","+str(item)+","+Checksum_Bloco(str(tipo),item)+"\n")
    Output.close()
#-----------------------------------------------------------------------------------------
#---------------------------------------------------------------------

#Engine
#-----------------------------------------------------------------------------------------
def Engine(Nome_PLC,IP,Rack,Slot):
    print("INICIANDO DETECTOR DE MODIFICACOES DE PROGRAMA DE PLC\n")
    Conectar_com_PLC(IP,Rack,Slot)

    diretorio_plc = str(diretorio_origem + Nome_PLC + "/")
    if not os.path.exists(diretorio_plc):
        os.mkdir(diretorio_plc)
    if not os.path.exists(str(diretorio_plc+"Historico/")):
        os.mkdir(str(diretorio_plc+"Historico/"))

    list_of_files = glob.glob(str(diretorio_plc+"Historico/"+"*.csv"))
    if not list_of_files: 
        with open(str(diretorio_plc+"Historico/new.csv"),'w') as first_log:
            first_log.write("Tipo,Indice,Checksums"+"\n")
        list_of_files = glob.glob(str(diretorio_plc+"Historico/"+"*.csv"))
    latest_file = max(list_of_files, key=os.path.getctime)
    shutil.copyfile(latest_file,str(diretorio_plc+"Historico/old.csv"))

    all_blocks_checksum_to_csv(diretorio_plc,IP)
    shutil.copyfile(str(diretorio_plc+"Historico/new.csv"),str(diretorio_plc+"Historico/"+str(date.today())+".csv"))

    compara_csv(str(diretorio_plc+"Historico/new.csv"),str(diretorio_plc+"Historico/old.csv"),str(diretorio_plc+"changelog.txt"))
    plc.disconnect()
#-----------------------------------------------------------------------------------------

#PRINCIPAL
#-----------------------------------------------------------------------------------------

Dados_de_entrada = csv.DictReader(open(str(diretorio_origem+"dados.csv")))
for row in Dados_de_entrada:
    Engine(row['Nome'],row['IP'],int(row['Rack']),int(row['Slot']))

input("Pressione ENTER para concluir execução")
print("Execução concluída\n")
#-----------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------