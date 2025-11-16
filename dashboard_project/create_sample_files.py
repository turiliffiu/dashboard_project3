import os

# Contenuti di esempio per i file
sample_contents = {
    'docker.txt': """[Comandi Base]
Gestione fondamentale di Docker

COMANDO: Lista container attivi
docker ps

COMANDO: Lista tutti i container
docker ps -a

COMANDO: Lista immagini
docker images

COMANDO: Rimuovi container
docker rm <container_id>

[Gestione Container]
Avvio, stop e riavvio dei container

COMANDO: Avvia container
docker start <container_id>

COMANDO: Ferma container
docker stop <container_id>

COMANDO: Logs in tempo reale
docker logs -f <container_id>
""",
    
    'linux.txt': """[Gestione File]
Operazioni su file e directory

COMANDO: Lista dettagliata
ls -lah

COMANDO: Copia ricorsiva
cp -r /sorgente /destinazione

COMANDO: Trova file
find /path -name "*.txt"

[Monitoraggio Sistema]
Verifica risorse e processi

COMANDO: Utilizzo disco
df -h

COMANDO: Memoria RAM
free -h

COMANDO: Processi attivi
top
""",
    
    'git.txt': """[Operazioni Base]
Comandi fondamentali Git

COMANDO: Inizializza repository
git init

COMANDO: Stato modifiche
git status

COMANDO: Aggiungi tutti i file
git add .

COMANDO: Commit
git commit -m "messaggio"

[Sincronizzazione]
Push e pull con remote

COMANDO: Push su main
git push origin main

COMANDO: Pull da remote
git pull origin main
"""
}

def create_sample_files():
    os.makedirs('procedure_files', exist_ok=True)
    
    for filename, content in sample_contents.items():
        filepath = os.path.join('procedure_files', filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'✓ Creato: {filepath}')

if __name__ == '__main__':
    create_sample_files()
    print('\\n✅ File di esempio creati con successo!')