"""
File contains all constants for easy central import and usage.
"""
CONFIGURATION_FILE_PATH = "../files/config.json"
DEVICES_FILE_PATH = "../files/devices.json"
CHAT_ID_FILE_PATH = "../files/chat_id.txt"
TIMEOUT_RESPONSE_TIME = 20
LOGGING_MAX_LEN_FAILURE = 5
TIME_OF_DAY_SCHEDULE_MATCH = r"^(?:[01]\d|2[0-3]):(?:[0-5]\d)$"
DAY_OF_MONTH_SCHEDULE_MATCH = r"^[\d]{2}$"
DATE_OF_YEAR_SCHEDULE_MATCH = r"^[\d]{2}[.][\d]{2}$"
DEFAULT_THRESHOLD_ON_POWER_ON_COUNTER = 2
DEFAULT_THRESHOLD_OFF_POWER_ON_COUNTER = 1
DEFAULT_BOT_UPDATE_TIME = 10
DEFAULT_BOT_REQUEST_HANDLE_TIME = 5
DEFAULT_INLINE_KEYS_COLUMNS = 3
USER_MESSAGE_INLINE_KEYBOARD_SET_ALARM = "Please select device:"
DEFAULT_REFERENCE_WH = 100
DEFAULT_ALARM_THRESHOLD_WH = DEFAULT_REFERENCE_WH * 1.2
DEFAULT_ALARM_PERIOD_MIN = 30
