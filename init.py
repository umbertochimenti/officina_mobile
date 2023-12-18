# init.py
import os
import subprocess

# Imposta la variabile d'ambiente
os.environ['SKLEARN_ALLOW_DEPRECATED_SKLEARN_PACKAGE_INSTALL'] = 'True'

# Esegui l'installazione delle dipendenze
subprocess.run(['pip', 'install', '-r', 'requirements.txt'])
