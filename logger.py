import logging
import coloredlogs
import inspect
import os
import sys
import threading
from functools import wraps
from pathlib import Path
import atexit
import tempfile
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def _get_log_level_from_env() -> int:
    """Parse LOG_LEVEL from environment variables with fallback to WARNING.
    
    Returns:
        Logging level constant (e.g., logging.DEBUG, logging.INFO, etc.)
    """
    log_level_str = os.getenv('LOG_LEVEL', 'DEBUG').upper().strip()
    
    # Map string values to logging constants
    level_mapping = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'WARN': logging.WARNING,  # Alternative spelling
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
        'FATAL': logging.CRITICAL,  # Alternative spelling
    }
    
    # Return the mapped level or default to WARNING
    return level_mapping.get(log_level_str, logging.WARNING)


# Thread-local storage for recursion detection
_thread_local = threading.local()

def _is_in_logging_call():
    """Check if we're already in a logging call to prevent recursion."""
    return getattr(_thread_local, 'in_logging_call', False)

def _set_logging_call_flag(value: bool):
    """Set the logging call flag for the current thread."""
    _thread_local.in_logging_call = value

def handle_recursion(func):
    """Decorator to handle potential recursion errors in logging functions"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Check if we're already in a logging call for this thread
        if _is_in_logging_call():
            return  # Silently return without logging to prevent recursion
            
        try:
            # Mark that we're in a logging call
            _set_logging_call_flag(True)
            
            # Execute the logging function
            result = func(self, *args, **kwargs)
            
            return result
            
        except RecursionError:
            # If recursion occurs, fall back to basic stderr output
            basic_msg = f"RECURSION ERROR while logging: {args[0] if args else ''}"
            try:
                # Last resort - direct stderr output without any logging
                app_logger.debug(basic_msg, file=sys.stderr)
            except:
                pass  # Silently fail if even stderr fails
            
        except Exception as e:
            try:
                app_logger.debug(f"Logging error: {str(e)}", file=sys.stderr)
            except:
                pass  # Silently fail if even stderr fails
        finally:
            # Always reset the flag when exiting
            _set_logging_call_flag(False)

    return wrapper

class Logger:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self, name='App', log_level=None, exc_info=True):
        if not hasattr(self, 'initialized'):
            # Use environment-based log level if not explicitly provided
            if log_level is None:
                log_level = _get_log_level_from_env()
            
            self.logger = logging.getLogger(name)
            self.logger.setLevel(log_level)
            
            # Ensure logger doesn't duplicate handlers
            if not self.logger.handlers:
                try:
                    # Get the log directory path
                    self.logs_dir = self._get_logs_directory()
                    self.logs_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Create rotating file handler
                    self._setup_file_handler()
                    
                    # Create console handler for development
                    if not getattr(sys, 'frozen', False):
                        self._setup_console_handler()
                    
                    # Register cleanup handler
                    atexit.register(self._cleanup_old_logs)
                    
                except Exception as e:
                    # Fallback to temporary directory if standard location fails
                    self._setup_fallback_logging()
                    
            self.initialized = True

    def _get_logs_directory(self):
        """Get the appropriate logs directory based on whether running as exe or script"""
        if getattr(sys, 'frozen', False):
            # If running as exe, use AppData
            base_dir = Path(os.getenv('APPDATA')) / 'ALPHA' / 'logs'
        else:
            # If running as script, use local logs directory
            base_dir = Path(__file__).parent.parent / 'logs'
        return base_dir

    def _setup_file_handler(self):
        """Setup the main file handler with rotation"""
        try:
            # Create log file with timestamp
            timestamp = datetime.now().strftime('%Y%m%d')
            log_file = self.logs_dir / f'app_{timestamp}.log'
            
            # Create file handler with UTF-8 encoding and immediate flush
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            
            # Simplified formatter
            file_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            
            # Enable immediate flushing
            file_handler.flush = lambda: True
            
            # Add handler to logger
            self.logger.addHandler(file_handler)
            
        except Exception as e:
            sys.stderr.write(f"Failed to setup file handler: {str(e)}\n")
            self._setup_fallback_logging()

    def _setup_console_handler(self):
        """Setup colored console output for development"""
        try:
            coloredlogs.install(
                level=self.logger.level,
                logger=self.logger,
                fmt='%(name)s - %(levelname)s - %(message)s',
                level_styles={
                    'debug': {'color': 'cyan', 'bold': True},
                    'info': {'color': 'green', 'bold': True}, 
                    'warning': {'color': 'yellow', 'bold': True},
                    'error': {'color': 'red', 'bold': True},
                    'critical': {'color': 'magenta', 'bold': True, 'background': 'red'},
                }
            )
        except Exception as e:
            sys.stderr.write(f"Failed to setup console handler: {str(e)}\n")

    def _setup_fallback_logging(self):
        """Setup fallback logging to temporary directory"""
        try:
            temp_dir = tempfile.gettempdir()
            fallback_log = os.path.join(temp_dir, 'alpha_fallback.log')
            
            # Create basic file handler
            handler = logging.FileHandler(fallback_log)
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            
            self.logger.addHandler(handler)
            self.logger.warning(f"Using fallback logging to: {fallback_log}")
            
        except Exception as e:
            sys.stderr.write(f"Failed to setup fallback logging: {str(e)}\n")

    def _cleanup_old_logs(self):
        """Clean up old log files (keeping last 7 days)"""
        try:
            if self.logs_dir.exists():
                current_time = datetime.now()
                for log_file in self.logs_dir.glob('app_*.log'):
                    try:
                        # Parse timestamp from filename
                        timestamp_str = log_file.stem.split('_')[1]
                        file_date = datetime.strptime(timestamp_str, '%Y%m%d')
                        
                        # Remove if older than 7 days
                        if (current_time - file_date).days > 7:
                            log_file.unlink()
                    except Exception:
                        continue
        except Exception:
            pass  # Silently fail cleanup

    def _get_caller_info(self):
        """Get the caller's frame info, handling potential recursion errors"""
        try:
            # Get the caller's frame info, skipping this function and the logging function
            frame = inspect.currentframe()
            if frame is None:
                return "unknown", "unknown"
            
            # Navigate up the call stack safely - skip fewer frames to be more reliable
            for _ in range(2):  # Skip this function and the logging method
                if frame.f_back is None:
                    return "unknown", "unknown"
                frame = frame.f_back
            
            filename = os.path.basename(frame.f_code.co_filename)
            func_name = frame.f_code.co_name
            
            return filename, func_name
            
        except Exception:
            return "unknown", "unknown"

    @handle_recursion
    def debug(self, message, exc_info=True):
        try:
            self.logger.debug(str(message))
        except Exception:
            self.logger.debug(str(message))

    @handle_recursion
    def info(self, message, exc_info=True):
        try:
            self.logger.info(str(message))
        except Exception:
            self.logger.info(str(message))

    @handle_recursion
    def warning(self, message, exc_info=True):
        try:
            self.logger.warning(str(message))
        except Exception:
            self.logger.warning(str(message))

    @handle_recursion
    def error(self, message, exc_info=True):
        try:
            self.logger.error(str(message), exc_info=exc_info)
        except Exception:
            self.logger.error(str(message), exc_info=exc_info)

    @handle_recursion
    def critical(self, message, exc_info=True):
        try:
            self.logger.critical(str(message))
        except Exception:
            self.logger.critical(str(message))

# Create a global logger instance using environment configuration
app_logger = Logger()

# Usage example:
# from utils.logger import app_logger
# app_logger.info("This is an info message")
