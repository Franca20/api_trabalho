from flask import Flask
from pathlib import Path

base_dir = Path(__file__).parent
templates = base_dir / 'templates'
static = base_dir / 'static'

app = Flask(__name__, template_folder=templates, static_folder=static)

from app.view import home
from app.view import carregar