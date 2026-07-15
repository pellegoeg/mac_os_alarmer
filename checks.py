import abc
import logging
from typing import Any

import psycopg2
import requests

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
        db_config: dict[str, Any],
        query: str,
        expected_value: float,
        operator: str = ">",
        alert_title_template: str = "SQL Alarm: {name}",
        alert_message_template: str = (
            "Betingelse opfyldt! Værdi: {value} (Forventet: {expected_value})"
        ),
    ):
        super().__init__(name)
        self.db_config = db_config
        self.query = query
        self.expected_value = expected_value
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
                        value=None,
                    )

                # Fetch first column
                val = row[0]
                if val is None:
                    return CheckResult(
                        is_alert=False,
                        title=self.name,
                        message="Returneret værdi var NULL.",
                        value=None,
                    )

                # Compare value with expected_value
                val_float = float(val)
                is_alert = False
                if self.operator == ">":
                    is_alert = val_float > self.expected_value
                elif self.operator == ">=":
                    is_alert = val_float >= self.expected_value
                elif self.operator == "<":
                    is_alert = val_float < self.expected_value
                elif self.operator == "<=":
                    is_alert = val_float <= self.expected_value
                elif self.operator == "==":
                    is_alert = val_float == self.expected_value
                elif self.operator == "!=":
                    is_alert = val_float != self.expected_value

                title = self.alert_title_template.format(
                    name=self.name, value=val, expected_value=self.expected_value
                )
                message = self.alert_message_template.format(
                    name=self.name, value=val, expected_value=self.expected_value
                )

                return CheckResult(
                    is_alert=is_alert, title=title, message=message, value=val
                )

        except Exception as e:
            logger.error(f"Fejl under kørsel af PostgreSQLCheck '{self.name}': {e}")
            return CheckResult(
                is_alert=True,
                title=f"Fejl i Check: {self.name}",
                message=f"Der opstod en databasefejl: {str(e)}",
                value=None,
            )
        finally:
            if conn:
                conn.close()


class RESTAPICheck(BaseCheck):
    def __init__(
        self,
        name: str,
        url: str,
        field: str,
        expected_value: Any,
        alert_title_template: str = "API Alarm: {name}",
        alert_message_template: str = (
            "Felt '{field}' har værdi {value}, forventet var {expected_value}"
        ),
    ):
        super().__init__(name)
        self.url = url
        self.field = field
        self.expected_value = expected_value
        self.alert_title_template = alert_title_template
        self.alert_message_template = alert_message_template

    def run(self) -> CheckResult:
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            data = response.json()

            actual_value = data.get(self.field)
            if actual_value is None:
                return CheckResult(
                    is_alert=True,
                    title=self.alert_title_template.format(name=self.name),
                    message=f"Felt '{self.field}' ikke fundet i response: {data}",
                    value=None,
                )

            is_alert = actual_value != self.expected_value
            title = self.alert_title_template.format(name=self.name)
            message = self.alert_message_template.format(
                name=self.name,
                field=self.field,
                value=actual_value,
                expected_value=self.expected_value,
            )

            return CheckResult(
                is_alert=is_alert, title=title, message=message, value=actual_value
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Fejl under kørsel af RESTAPICheck '{self.name}': {e}")
            return CheckResult(
                is_alert=True,
                title=f"Fejl i Check: {self.name}",
                message=f"Der opstod en HTTP-fejl: {str(e)}",
                value=None,
            )
        except Exception as e:
            logger.error(f"Fejl under kørsel af RESTAPICheck '{self.name}': {e}")
            return CheckResult(
                is_alert=True,
                title=f"Fejl i Check: {self.name}",
                message=f"Der opstod en fejl: {str(e)}",
                value=None,
            )
