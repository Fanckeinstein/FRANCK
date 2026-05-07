from flask import Blueprint

bp = Blueprint('verification', __name__)

from . import routes  # noqa: E402, F401
