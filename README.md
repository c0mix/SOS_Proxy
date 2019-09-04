# SOS_Proxy

Problema: hai un device su cui non riesci a impostare un proxy per sniffare il traffico.

Setup: pc con 2 interfacce di rete "eth0" connesso a Internet e "wlan0" in modalità hotspot con il device collegato.

Soluzione: utilizzare la tecnica del DNS spoofing + invisible proxy per far passare il traffico da BURP (https://portswigger.net/burp/documentation/desktop/tools/proxy/options/invisible)

Problematiche associate alla soluzione proposta:

Per ciascun domino che il device richiede è necessario eseguire le seguenti operazioni:
1. bisogna creare una interfaccia di rete virtuale
2. bisogna mappare il dominio sull'interfaccia tramite modifica di /etc/hosts in modo tale che le richieste che il device fa a pippo.com andranno non più a 68.66.200.200 (vero IP di pippo.com) ma a una interfaccia virtuale sul mio host es. 100.100.100.1
3. si deve creare un nuovo proxy all'interno di burp (a mano)
4. si deve gestire il redirect da parte di burp al vero ip del dominio e gli eventuali errori di cert ssl (a mano)

Il tool automatizza i primi due punti e fornisce un output dettagliato su come impostare i vari proxy di burp.

Oltre alle funzionalità base il tool:
- Ripulisce la configurazione alla fine dei test
- Consente il salvataggio del file hosts, nel caso si voglia riprendere l'analisi in un secondo momento
- In modalità ask "-a" chiede se un dominio vada o meno intercettato
- E' in grado di ripristinare "-r" una configurazione e di continuare l'attività da dove la si era lasciata

## Dipendenze
- tmux
- ifconfig
- python 2.7
- tcpdump

## NOTE
- Il tool è molto quick & dirty, testato solo su *ubuntu* e, attualmente, scarsamente mantenuto
- Il setup del lab per il testing suggerito in alto non è obbligatorio ma probabilmente è quello più "pulito" per analizzare il device.
- Il tool non è stato testato a fondo quindi: be careful :) usate -a e -v per capire che sta succedendo ed i seguenti comandi come debug:
    - $ tail -f /tmp/domains <- file dove vengono stampati i domini trovati da tcpdump
    - $ watch -n 2 ifconfig <- per vedere se le interfacce virtuali vengono create
    - $ sudo tmux att -t Domain_Monitor <- per vedere se tmux con tcpdump è in esecuzione
