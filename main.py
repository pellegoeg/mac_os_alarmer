import os
import json
import logging
from dotenv import load_dotenv
from notifiers import MacNotifier, TeamsNotifier
from checks import PostgreSQLCheck, RESTAPICheck

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.expanduser("~/Library/Logs/mac_os_alarmer.log"))
    ]
)
logger = logging.getLogger("alarmer")

def load_config():
    load_dotenv()
    
    # Default configuration path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "config.json")
    
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            logger.info(f"Konfiguration indlæst fra {config_path}")
        except Exception as e:
            logger.error(f"Fejl ved indlæsning af {config_path}: {e}")
            
    return config

def main():
    config = load_config()
    
    # Configure notifier
    notifier_config = config.get("notifier", {})
    notifier_type = os.getenv("NOTIFIER_TYPE", notifier_config.get("type", "mac"))
    
    if notifier_type == "teams":
        webhook_url = os.getenv("TEAMS_WEBHOOK_URL", notifier_config.get("teams_webhook_url"))
        if not webhook_url:
            logger.error("TEAMS_WEBHOOK_URL er ikke sat, falder tilbage til macOS-notifikationer.")
            notifier = MacNotifier(
                sound_name=notifier_config.get("sound_name", "Glass"),
                timeout=notifier_config.get("timeout", 0)
            )
        else:
            notifier = TeamsNotifier(webhook_url=webhook_url)
    else:
        notifier = MacNotifier(
            sound_name=notifier_config.get("sound_name", "Glass"),
            timeout=notifier_config.get("timeout", 0)
        )
        
    # Configure database settings
    db_config = config.get("database", {})
    # Allow environment variables to override or set database details
    db_params = {
        "host": os.getenv("DB_HOST", db_config.get("host", "localhost")),
        "port": int(os.getenv("DB_PORT", db_config.get("port", 5432))),
        "database": os.getenv("DB_NAME", db_config.get("database", db_config.get("dbname", "postgres"))),
        "user": os.getenv("DB_USER", db_config.get("user", "postgres")),
        "password": os.getenv("DB_PASSWORD", db_config.get("password", ""))
    }
    
    # Configure checks
    checks_list = config.get("checks", [])
    if not checks_list:
        # Default fallback check if config is empty (matching the user request)
        checks_list = [
            {
                "name": "Base Tables Last Extracted",
                "type": "postgresql",
                "query": "SELECT extract(days from NOW()-extracted_at) as dage_siden FROM openstack.assert_base_tables_last_extracted_at order by extracted_at DESC LIMIT 1",
                "threshold": 0.0,
                "operator": ">",
                "alert_title": "Data Extraction Forsinket",
                "alert_message": "Der er gået {value} dage siden sidste base table extraction (grænse: {threshold} dage)."
            }
        ]
        
    for check_def in checks_list:
        check_type = check_def.get("type", "postgresql")
        name = check_def.get("name", "Ubenævnt Check")
        
        if check_type == "postgresql":
            check = PostgreSQLCheck(
                name=name,
                db_config=db_params,
                query=check_def["query"],
                expected_value=check_def.get("expected_value", 0.0),
                operator=check_def.get("operator", ">"),
                alert_title_template=check_def.get("alert_title", "SQL Alarm: {name}"),
                alert_message_template=check_def.get("alert_message", "Betingelse opfyldt! Værdi: {value} (Forventet: {expected_value})")
            )
        elif check_type == "restapi":
            check = RESTAPICheck(
                name=name,
                url=check_def["url"],
                field=check_def["field"],
                expected_value=check_def["expected_value"],
                alert_title_template=check_def.get("alert_title", "API Alarm: {name}"),
                alert_message_template=check_def.get("alert_message", "Felt '{field}' har værdi {value}, forventet var {expected_value}")
            )
        else:
            logger.warning(f"Ukendt check type: {check_type}")
            continue
            
        logger.info(f"Kører check: {name}")
        result = check.run()
        
        if result.is_alert:
            logger.warning(f"Alarm udløst for '{name}': {result.message}")
            notifier.notify(result.title, result.message)
        else:
            logger.info(f"Check '{name}' er OK. Værdi: {result.value}")

if __name__ == "__main__":
    main()
