import os

path=input("Arraste aqui o programa que deve ser compilado para .exe: \n")
path=path.replace("str(\)","str(/)")
cmd = str("pyinstaller "+path+" --onefile")

os.system(cmd)
