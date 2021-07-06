from subprocess import call
import webbrowser
import threading
import time

comando = 'python3 app3.py'
address = 8050

def start_sub():
    result = None
    while result is None:
        try:
            call(comando, shell=True)
        except Exception as e:
            print(e)
            pass
        else:
            result = 'Sì'

t = threading.Thread(target=start_sub)
t.start()
print('apro pagina web')
time.sleep(12)
webbrowser.open('http://127.0.0.1:8051/', new=0)
