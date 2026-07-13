import logging
from notifiers import MacNotifier

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_mac_notification():
    print("Tester macOS systemnotifikation...")
    notifier = MacNotifier(sound_name="Glass")
    notifier.notify("Test Alarm", "Dette er en test-notifikation fra mac_os_alarmer!")
    print("Notifikation sendt! Fik du en popup på din skærm?")

if __name__ == "__main__":
    test_mac_notification()
