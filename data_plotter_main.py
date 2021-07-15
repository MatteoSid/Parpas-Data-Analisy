from subprocess import call
import webbrowser
import threading
import time

comando = 'python3 table_new.py'
address = 8050

def start_sub():
    while True:
        try:
            call(comando, shell=True)
        except Exception as e:
            print(e)
            pass
        else:
            break

t = threading.Thread(target=start_sub)
t.start()
#print('apro pagina web')
time.sleep(3)
webbrowser.open('http://127.0.0.1:' + str(address) + '/', new=0)
