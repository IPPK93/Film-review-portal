import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.security import HTTPBasic

from . import models
from .database import engine

load_dotenv()


def init_paths() -> None:
    log_dir = os.environ.get('LOG_DIR')
    log_file = os.environ.get('LOG_FILE')

    if log_dir is not None:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
    if log_file is not None:
        logging.basicConfig(filename=log_file)


init_paths()
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
security = HTTPBasic()
