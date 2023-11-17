import sqlite3
from sqlite3 import Error
import pathlib

diretorio_origem = str(pathlib.Path(__file__).parent.absolute())

try: 
    database=sqlite3.connect(str(diretorio_origem+'/Teste'))
except Error as e:
    print(e)

def Query_database(sql_query):
    result=database.cursor().execute(sql_query)    
    database.commit()
    return result

Query_database("""SELECT name FROM sqlite_master 
WHERE type='table';""")

Query_database("""DELETE FROM Checksums 
WHERE id = 'plc_1';""")

Query_database("""INSERT INTO Checksums (id, block_Type, block_index, Checksum_online) 
VALUES ("plc_1","FB",1,3457);""")

Query_database("""UPDATE Checksums SET Checksum_offline = '1234' WHERE id = 'plc_1';""")

table = Query_database("""SELECT * FROM Checksums;""")
for row in table:
    print(row)

