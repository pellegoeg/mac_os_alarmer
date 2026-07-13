import abc
import subprocess
import requests
import logging

logger = logging.getLogger(__name__)

class BaseNotifier(abc.ABC):
    @abc.abstractmethod
    def notify(self, title: str, message: str) -> None:
        """Sends a notification with a title and message."""
        pass

class MacNotifier(BaseNotifier):
    def __init__(self, sound_name: str = "Glass", timeout: int = 0):
        self.sound_name = sound_name
        self.timeout = timeout

    def notify(self, title: str, message: str) -> None:
        # Escape double quotes for AppleScript string syntax
        escaped_title = title.replace('"', '\\"')
        escaped_message = message.replace('"', '\\"')
        
        if self.timeout > 0:
            script = f'display dialog "{escaped_message}" with title "{escaped_title}"'
            script += f' giving up after {self.timeout}'
        else:
            script = f'display notification "{escaped_message}" with title "{escaped_title}"'
            if self.sound_name:
                script += f' sound name "{self.sound_name}"'
            
        cmd = ["osascript", "-e", script]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Mac Notification sent: {title} - {message}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to send Mac notification: {e.stderr.decode().strip()}")

class TeamsNotifier(BaseNotifier):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def notify(self, title: str, message: str) -> None:
        if not self.webhook_url:
            logger.warning("Teams webhook URL not configured, skipping notification.")
            return

        payload = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "type": "AdaptiveCard",
                        "body": [
                            {
                                "type": "TextBlock",
                                "size": "Medium",
                                "weight": "Bolder",
                                "text": title
                            },
                            {
                                "type": "TextBlock",
                                "text": message,
                                "wrap": True
                            }
                        ],
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "version": "1.2"
                    }
                }
            ]
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Teams notification sent: {title}")
        except requests.RequestException as e:
            logger.error(f"Failed to send Teams notification: {e}")
