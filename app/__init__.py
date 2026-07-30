from flask import Flask
from pathlib import Path
from dotenv import load_dotenv

base_dir = Path(__file__).parent
load_dotenv(base_dir.parent / '.env')
templates = base_dir / 'templates'
static = base_dir / 'static'

app = Flask(__name__, template_folder=templates, static_folder=static)

from app.view import home
from app.view import carregar