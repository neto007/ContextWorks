import logging
import sys
import os
import json
import contextvars
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Configuração de diretório de logs
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, "backend.log")

# Variável de contexto para rastreabilidade (Request ID)
request_id_ctx = contextvars.ContextVar("request_id", default=None)

# Habilitar JSON por padrão se não estiver em ambiente de dev
USE_JSON_LOGS = os.getenv("USE_JSON_LOGS", "true").lower() == "true"

class JSONFormatter(logging.Formatter):
    """Formatador de logs em JSON para nível Enterprise"""
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        
        # Adicionar Request ID automático da ContextVar
        rid = request_id_ctx.get()
        if rid:
            log_record["request_id"] = rid
        elif hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
            
        # Adicionar campos extras incluídos via extra={}
        if hasattr(record, "extra_fields"):
            log_record.update(record.extra_fields)
            
        # Se houver exceção, formatar o traceback
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

def setup_logger(name: str):
    """Configura um logger estruturado (JSON ou Texto)"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if logger.handlers:
        return logger

    # Determinar o formatador
    if USE_JSON_LOGS:
        formatter = JSONFormatter()
    else:
        # Formato legível para humanos em desenvolvimento
        log_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        formatter = logging.Formatter(log_format)

    # Handler para console (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler para arquivo (com rotação)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# Logger principal
logger = setup_logger("security-platform")
