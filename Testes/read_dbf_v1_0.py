import dbfread
from dbfread import DBF
import sqlite3

con=sqlite3.connect('/home/filipe/Downloads/VW GUIA BAJO FARO_V14_20190502/XRef/XRef.db')
cur=con.cursor()


    # Getting all tables from sqlite_master
sql_query = """SELECT name FROM sqlite_master
WHERE type='table';"""
 
     
    # executing our sql query
cur.execute(sql_query)
print("List of tables\n")
     
    # printing all tables list
print(cur.fetchall())
#for row in 
sql_query = """SELECT * FROM rels;"""

for row in cur.execute(sql_query):
    print(row)

exit()


endereco = '/home/filipe/Downloads/Copy of Mfs_VW_1/ombstx/offline/00000001/checksums.csv' 
table=DBF('/home/filipe/Downloads/Copy of Mfs_VW_1/ombstx/offline/00000001/SUBBLK.dbf',raw=True)



print("Gerando banco de dados de checksums dos blocos no backup offline"+"\n")
Output = open((endereco), "w")
Output.write("Tipo,Indice,Checksums"+"\n")
for record in table:
    if int(record['SUBBLKTYP'])==8:
        tipo='OB'
        indice=int(record['BLKNUMBER'])
        Checksum_Bloco=int(record['CHECKSUM'])
        Output.write(str(tipo)+","+str(indice)+","+str(Checksum_Bloco)+"\n")
    if int(record['SUBBLKTYP'])==12:
        tipo='FC'
        indice=int(record['BLKNUMBER'])
        Checksum_Bloco=int(record['CHECKSUM'])
        Output.write(str(tipo)+","+str(indice)+","+str(Checksum_Bloco)+"\n")
    if int(record['SUBBLKTYP'])==14:
        tipo='FB'
        indice=int(record['BLKNUMBER'])
        Checksum_Bloco=int(record['CHECKSUM'])
        Output.write(str(tipo)+","+str(indice)+","+str(Checksum_Bloco)+"\n")        
Output.close()


