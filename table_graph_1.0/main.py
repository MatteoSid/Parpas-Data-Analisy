from subprocess import call
import webbrowser
import threading
import time
import os

def tab_to_df(filename):
        
    file1 = open(filename, "rb")
    df = pd.DataFrame()
    flag_data = 0
    
    pbar = tqdm(file1, desc=filename)
    for line in pbar:

        if b'\xb0C' in line:     # se trovo il carattere °C lo ignoro
            pass
        else:
            line = line.decode() # altrimenti decodifico la riga

            # cerco la riga con i nomi della tabella
            if line.startswith('NR'):
                flag_data = 1                  # quando trovo i nomi delle colonne imposto flag_data = 1
                table_names = line.split()     # divido i nomi delle colonne      
                table_names.remove('LastLine') # elimino 'LastLine' che fa riferimento ad un singolo dato duplicato
                
                # definisco i nomi delle colonne del dataframe
                df = df.reindex(columns = table_names)

            # Se sono arrivato alla tabella ma la riga inizia con 0 la salto
            elif flag_data == 1 and line.startswith('0'):
                pass

            # Se sono arrivato alla tabella (flag_data == 1) e non sono alla prima riga
            # inizio a salvare i dati
            elif flag_data == 1:
                row = line.split()

                if not line.startswith('[END]') and len(row) == len(table_names)+1: # le righe con meno di 25 elementi hanno dati mancanti
                    row[-2] = str(row[-2]) + ' ' + str(row[-1]) # unisco l'ora col giorno
                    del row[-1] # elimino la colonna con i giorni
                    
                    df_length = len(df)
                    df.loc[df_length] = row
    
    #df['DataTime'] = pd.to_datetime(df['DataTime'], format='%H:%M:%S %d.%m.%y', errors='coerce')
    df.set_index('DataTime', drop = True, inplace=True)
    df.index = pd.to_datetime(df.index, format='%H:%M:%S %d.%m.%Y')
    df.drop('NR', axis=1, inplace=True)
    
    for column in df.keys():
        if 'PLC_Byt' in column or column == 'OpMode':
            df.drop(column, axis=1, inplace=True)
        else:
            df[column] = df[column].apply(pd.to_numeric)
    return df

os.system('clear')
comando = 'python3 app.py'
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

path = 'table/'
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
