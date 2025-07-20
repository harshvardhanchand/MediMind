import logging
import os
import json
import sys
from typing import Dict, Any, Optional

import google.cloud.logging
from google.cloud.logging_v2.handlers import CloudLoggingHandler

from app.core.config import settings

class StructuredLogRecord(logging.LogRecord):
    """
    Custom LogRecord that adds structured data to log entries.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.structured_data = {}

    def set_structured_data(self, data: Dict[str, Any]) -> None:
        """
        Add structured data to the log record.
        
        Args:
            data: Dictionary of data to add to the log record
        """
        self.structured_data.update(data)


class StructuredLogger(logging.Logger):
    """
    Custom logger that supports structured logging.
    """
    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None):
        record = StructuredLogRecord(name, level, fn, lno, msg, args, exc_info, func, sinfo)
        if extra:
            for key in extra:
                if key == "structured_data" and isinstance(extra[key], dict):
                    record.set_structured_data(extra[key])
                else:
                    setattr(record, key, extra[key])
        return record


class StructuredFormatter(logging.Formatter):
    """
    Formatter that outputs logs in a structured JSON format.
    """
    def format(self, record: StructuredLogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger_name": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        
        if hasattr(record, "structured_data") and record.structured_data:
            log_data.update(record.structured_data)
            
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)


def setup_logging(level: Optional[str] = None) -> None:
    """
    Set up application logging with appropriate handlers based on environment.
    
    Args:
        level: Optional override for the log level
    """
    
    log_level = getattr(logging, level or settings.LOG_LEVEL)
    
    
    logging.setLoggerClass(StructuredLogger)
    
    
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Clear existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    
    if (settings.ENVIRONMENT == "production" and 
            settings.GCP_PROJECT_ID and 
            os.path.exists(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", ""))):
        try:
            client = google.cloud.logging.Client(
                project=settings.GCP_PROJECT_ID
            )
            handler = CloudLoggingHandler(client)
            logger.addHandler(handler)
            logger.info("Google Cloud Logging configured", 
                      extra={"structured_data": {"environment": settings.ENVIRONMENT,"project_id": settings.GCP_PROJECT_ID}})
        except Exception as e:
            # Fallback to standard logging
            handler = logging.StreamHandler(sys.stdout)
            formatter = StructuredFormatter()
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.error(f"Failed to set up Google Cloud Logging: {str(e)}", 
                       extra={"structured_data": {"environment": settings.ENVIRONMENT,"project_id": settings.GCP_PROJECT_ID}})
    else:
        
        handler = logging.StreamHandler(sys.stdout)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.info("Local logging configured", 
                  extra={"structured_data": {"environment": settings.ENVIRONMENT}}) 