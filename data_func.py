import pandas as pd
import csv
import os
from tqdm import tqdm

def txt_to_csv(filename, filedest):
    if os.path.isfile(filedest + '.csv'):
        os.remove(filedest + '.csv')
        
    file1 = open(filename + '.txt', "rb")
    file_csv = open(filedest + '.csv', 'w+', newline ='')

    count = 0
    flag_data = 0

    with file_csv:
        for line in file1:

            if b'\xb0C' in line:     # se trovo il carattere °C lo ignoro
                pass
            else:
                line = line.decode() # altrimenti decodifico la riga

                # cerco la riga con i nomi della tabella
                if line.startswith('NR'):
                    flag_data = 1                  # quando trovo i nomi delle colonne imposto flag_data = 1
                    table_names = line.split()     # divido i nomi delle colonne      
                    table_names.remove('LastLine') # elimino 'LastLine' che fa riferimento ad un singolo dato duplicato
                    #for item in table_names: print(item)
                    write = csv.writer(file_csv)  
                    write.writerow(table_names)
                    #print(table_names)

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
                        write = csv.writer(file_csv)
                        write.writerow(row)
                        count = count+1      # aggiorno il contatore delle righe

def load_data(file):
    #column_subset = ['t_Mach',   't_HydrTa', 't_TTlubr', 't_TT_ab1', 
                     #'t_TT_ab2', 't_HdStUp', 't_HdStLw', 't_Sfrnt1', 
                     #'t_Sfrnt2', 't_Srear',  't_Smotor', 'DataTime']

    df = pd.read_csv (file,
                      #usecols=column_subset,
                      index_col=False)

    df['DataTime'] = pd.to_datetime(df['DataTime'], format='%H:%M:%S %d.%m.%Y')
    
    df.set_index('DataTime', drop = True, inplace=True)
    
    if not df.index.is_monotonic:
        df.sort_index(inplace = True)
    
    df.drop('NR', axis=1, inplace=True)
    
    return df

def create_single_csv(path_folder, tab_name):
    data_list=[]

    for filename in os.listdir(path_folder):
        if tab_name in filename: 
            data = load_data(path_folder + 'csv/' + filename[:-4] + '.csv')
            data_list.append(data)

    data_all = pd.concat(data_list)
    data_all.sort_index(inplace = True)
    data_all.to_csv(path_folder + '/csv/' + tab_name + '_all.csv')

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
                        