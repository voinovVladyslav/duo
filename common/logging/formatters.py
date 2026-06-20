import logging

RESET = '\033[0m'

BLACK = '\033[30m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
MAGENTA = '\033[35m'
CYAN = '\033[36m'
WHITE = '\033[37m'

BRIGHT_BLACK = '\033[90m'
BRIGHT_RED = '\033[91m'
BRIGHT_GREEN = '\033[92m'
BRIGHT_YELLOW = '\033[93m'
BRIGHT_BLUE = '\033[94m'
BRIGHT_MAGENTA = '\033[95m'
BRIGHT_CYAN = '\033[96m'
BRIGHT_WHITE = '\033[97m'

BOLD = '\033[1m'
DIM = '\033[2m'
UNDERLINE = '\033[4m'

LEVEL_COLORS = {
    'DEBUG': BRIGHT_BLACK,
    'INFO': CYAN,
    'WARNING': YELLOW,
    'ERROR': RED,
    'CRITICAL': BOLD + RED,
}


class ColorfulFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        levelname = record.levelname
        name = record.name
        color = LEVEL_COLORS.get(record.levelname, '')
        padded = f'{record.levelname:<8}'
        record.levelname = f'{color}{padded}{RESET}'
        record.name = f'{BOLD + DIM}{record.name}{RESET}'
        try:
            return super().format(record)
        finally:
            # restore original values after applying color
            record.levelname = levelname
            record.name = name

