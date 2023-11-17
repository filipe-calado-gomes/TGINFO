import snap7 #interface com PLC
plc = snap7.client.Client()

def Conectar_com_PLC(IP_do_PLC,Numero_do_Rack,Numero_do_slot):
    plc.connect(IP_do_PLC,Numero_do_Rack,Numero_do_slot)
    Status_de_conexao = (plc.get_connected())
    if Status_de_conexao == True:
        print('Conexão em '+IP_do_PLC+' estabelecida com sucesso\n')
    else:
        print ('Há problemas na conexão com o PLC\n')
        input()
#---------------------------------------------------------------------

plc.connect("192.168.50.212",0,2)

tipos = ['OB','FB','FC','DB']
for tipo in tipos:
    indices_do_tipo = plc.list_blocks_of_type(str(tipo),1000)
    for item in indices_do_tipo:
        plc.delete(tipo,item)

