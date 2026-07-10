# mac_os_alarmer

Et lille, modulært Python-program til macOS, som kører baggrundschecks (f.eks. SQL-forespørgsler mod en database) og sender alarmer via systemnotifikationer eller Microsoft Teams, hvis en betingelse er opfyldt.

Programmet kører automatisk ved opstart af din Mac og derefter i intervaller (standard: hvert 30. minut) ved hjælp af en indbygget macOS LaunchAgent.

---

## Indholdsfortegnelse
1. [Hurtig Opstart](#hurtig-opstart)
2. [Konfiguration](#konfiguration)
3. [Hvordan man tilføjer notifikationer til andre brugere](#hvordan-man-tilføjer-notifikationer-til-andre-brugere)
4. [Udvidelse med nye checks eller kanaler](#udvidelse-med-nye-checks-eller-kanaler)

---

## Hurtig Opstart

1. **Hent projektet og gå til mappen:**
   ```bash
   cd /Users/HY87FR/Projects/pellegoeg/mac_os_alarmer
   ```

2. **Kør installations-scriptet:**
   ```bash
   ./install_launchagent.sh
   ```
   *Dette vil automatisk oprette et virtuelt Python-miljø (`.venv`), installere afhængigheder, oprette en standard `config.json` samt installere og starte LaunchAgenten.*

3. **Verificer logfiler:**
   Du kan se logudskrifter og eventuelle fejl her:
   ```bash
   tail -f ~/Library/Logs/com.user.mac_os_alarmer.stdout.log
   tail -f ~/Library/Logs/com.user.mac_os_alarmer.stderr.log
   ```

---

## Konfiguration

Konfigurationen styres via `config.json`. Du kan også bruge en `.env`-fil til at holde følsomme oplysninger såsom databaseadgangskoder eller webhook-URL'er.

### Eksempel på `config.json`
```json
{
  "notifier": {
    "type": "mac",
    "sound_name": "Glass",
    "teams_webhook_url": ""
  },
  "database": {
    "host": "localhost",
    "port": 5432,
    "dbname": "openstack",
    "user": "postgres",
    "password": ""
  },
  "checks": [
    {
      "name": "Base Tables Last Extracted",
      "type": "postgresql",
      "query": "SELECT extract(days from NOW()-extracted_at) as dage_siden FROM openstack.assert_base_tables_last_extracted_at order by extracted_at DESC LIMIT 1",
      "threshold": 0.0,
      "operator": ">",
      "alert_title": "Data Extraction Forsinket",
      "alert_message": "Der er gået {value} dage siden sidste base table extraction."
    }
  ]
}
```

---

## Hvordan man tilføjer notifikationer til andre brugere

Hvis du vil have programmet til at alarmere andre brugere eller kollegaer, er der tre primære metoder:

### Metode 1: Send notifikationer til en delt Microsoft Teams-kanal (Anbefalet)
Den nemmeste måde at dele alarmer med andre brugere på er at sende dem til en fælles chat eller kanal i Teams.
1. Hent en **Incoming Webhook URL** for din Teams-kanal/chat.
2. Sæt `NOTIFIER_TYPE=teams` i din `.env`-fil eller `"type": "teams"` i `config.json`.
3. Indsæt webhook URL'en under `TEAMS_WEBHOOK_URL` i din `.env`-fil eller `teams_webhook_url` i `config.json`.
4. Alle medlemmer af Teams-kanalen vil nu modtage alarmerne samtidigt.

### Metode 2: Kør programmet lokalt på andre brugeres Macs
Hvis andre brugere skal have personlige macOS-systemnotifikationer (popups på deres egen skærm):
1. Klon dette repository på den anden brugers Mac.
2. Kør `./install_launchagent.sh` på deres maskine.
3. Konfigurer deres lokale `config.json` til at forbinde til den fælles database.
4. Programmet vil nu køre uafhængigt som en LaunchAgent på deres Mac og give dem lokale popups.

### Metode 3: Udvid med andre modtagere (f.eks. Slack, E-mail eller SMS)
Hvis du vil sende notifikationer til andre brugere via andre tjenester, kan du nemt tilføje en ny *Notifier*-klasse i `notifiers.py`.

Eksempel på en Slack notifier:
```python
class SlackNotifier(BaseNotifier):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def notify(self, title: str, message: str) -> None:
        payload = {"text": f"*{title}*\n{message}"}
        requests.post(self.webhook_url, json=payload)
```
Derefter kan du registrere den i `main.py` på samme måde som Teams-notifikationer.

---

## Udvidelse med nye checks eller kanaler

1. **Flere SQL-checks**: Du kan tilføje lige så mange checks du vil i `checks`-listen i `config.json`. De vil blive afviklet i rækkefølge.
2. **Andre datakilder**: For at lave et API-tjek eller lignende, kan du oprette en ny klasse i `checks.py` (f.eks. `class APICheck(BaseCheck)`), som arver fra `BaseCheck` og implementerer `run()`-metoden.
