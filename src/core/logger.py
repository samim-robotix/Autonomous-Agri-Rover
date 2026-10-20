"""
Custom Colorized Logging System for Agriculture Rover.
Provides timestamped, categorized telemetry logs across hardware, vision, and navigation.
"""

import sys
import logging
from datetime import datetime

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False

class ColoredFormatter(logging.Formatter):
    """Formats log records with ANSI colors based on log severity and component."""
    
    COLORS = {
        logging.DEBUG: Fore.CYAN if HAS_COLORAMA else "",
        logging.INFO: Fore.GREEN if HAS_COLORAMA else "",
        logging.WARNING: Fore.YELLOW if HAS_COLORAMA else "",
        logging.ERROR: Fore.RED if HAS_COLORAMA else "",
        logging.CRITICAL: Fore.RED + Style.BRIGHT if HAS_COLORAMA else ""
    }
    RESET = Style.RESET_ALL if HAS_COLORAMA else ""

    def format(self, record):
        color = self.COLORS.get(record.levelno, "")
        log_time = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3]
        prefix = f"[{log_time}] [{record.levelname:<7}] [{record.name}]"
        return f"{color}{prefix} {record.getMessage()}{self.RESET}"

def get_rover_logger(name: str = "ROVER", level: int = logging.INFO) -> logging.Logger:
    """Returns a pre-configured rover logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColoredFormatter())
        logger.addHandler(console_handler)
    return logger
