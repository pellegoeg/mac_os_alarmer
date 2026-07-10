import abc
import logging
import psycopg2
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class CheckResult:
    def __init__(self, is_alert: bool, title: str, message: str, value: Any = None):
        self.is_alert = is_alert
        self.title = title
        self.message = message
        self.value = value

class BaseCheck(abc.ABC):
    def __init__(self, name: str):
        self.name = name

    @abc.abstractmethod
    def run(self) -> CheckResult:
        """Runs the check and returns a CheckResult."""
        pass

class PostgreSQLCheck(BaseCheck):
    def __init__(
        self,
        name: str,
        db_config: Dict[str, Any],
        query: str,
        threshold: float,
        operator: str = ">",
        alert_title_template: str = "SQL Alarm: {name}",
        alert_message_template: str = "Betingelse opfyldt! Værdi: {value} (Grænseværdi: {threshold})"
    ):
        super().__init__(name)
        self.db_config = db_config
        self.query = query
        self.threshold = threshold
        self.operator = operator
        self.alert_title_template = alert_title_template
        self.alert_message_template = alert_message_template

    def run(self) -> CheckResult:
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor() as cur:
                cur.execute(self.query)
                row = cur.fetchone()
                if row is None:
                    return CheckResult(
                        is_alert=False,
                        title=self.name,
                        message="Ingen data returneret af forespørgslen.",
                        value=None
                    )
                
                # Fetch first column
                val = row[0]
                if val is None:
                    return CheckResult(
                        is_alert=False,
                        title=self.name,
                        message="Returneret værdi var NULL.",
                        value=None
                    )
                
                # Compare value with threshold
                val_float = float(val)
                is_alert = False
                if self.operator == ">":
                    is_alert = val_float > self.threshold
                elif self.operator == ">=":
                    is_alert = val_float >= self.threshold
                elif self.operator == "<":
                    is_alert = val_float < self.threshold
                elif self.operator == "<=":
                    is_alert = val_float <= self.threshold
                elif self.operator == "==":
                    is_alert = val_float == self.threshold
                elif self.operator == "!=":
                    is_alert = val_float != self.threshold
                
                title = self.alert_title_template.format(name=self.name, value=val, threshold=self.threshold)
                message = self.alert_message_template.format(name=self.name, value=val, threshold=self.threshold)
                
                return CheckResult(is_alert=is_alert, title=title, message=message, value=val)
                
        except Exception as e:
            logger.error(f"Fejl under kørsel af PostgreSQLCheck '{self.name}': {e}")
            return CheckResult(
                is_alert=True,
                title=f"Fejl i Check: {self.name}",
                message=f"Der opstod en databasefejl: {str(e)}",
                value=None
            )
        finally:
            if conn:
                conn.close()
