# Distributed Cluster

## Comandi eseguiti:
- `poetry init`: serve per creare il file `pyproject.toml`, al cui interno si trova il nome del progetto, la versione, le dipendenze e le configurazioni.
- `poetry add --group dev pytest`: aggiunge *pytest* per la realizzazione dei test.

## Architettura:
Si tratta di un sistema di tipo *event-driven*.
- **Common**: contiene il message type, l'event type, la struttura dati del task e le funzioni di encode e decode per il json.
- **Dispatcher**: contenuto in ogni singolo nodo, mappa l'event type nell'handler corrispondente.
- **Handlers**: ricevono il messaggio e producono un evento.
- **Bootstrap**: rappresenta il main del Coordinator e dei Worker, si occupa di creare il dispatcher, di registrare gli handler e di avviare il loop legato alla rete.