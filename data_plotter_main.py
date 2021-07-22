from subprocess import call
import webbrowser
import threading
import time
import os
from data_func import tab_to_df

comando = 'python3 app4.py'
address = 8051

def start_sub():
    while True:
        try:
            call(comando, shell=True)
        except Exception as e:
            print(e)
            pass
        else:
            break

path = 'table_new2/'
path_dest = path + 'csv/'
dataDict = {}
if not os.path.isdir(path_dest):
    print('\nTrasformo le tabelle per la visualizzazione, potrebbe richiedere qualche minuto...\n')
    os.mkdir(path_dest)
    for filename in os.listdir(path):
        if (filename.endswith('.txt') or filename.endswith('.tab')): 
            df = tab_to_df(path + filename)
            if len(df) > 5:
                #df = df.resample('10T').mean()
                df.sort_index(inplace = True)
                dataDict[filename] = df
                df.to_csv(path_dest+filename, index=True)

    for i in dataDict:
        print(i)

if os.path.isdir(path_dest):
    t = threading.Thread(target=start_sub)
    t.start()
    #print('apro pagina web')
    time.sleep(3)
    webbrowser.open('http://127.0.0.1:' + str(address) + '/', new=0)
