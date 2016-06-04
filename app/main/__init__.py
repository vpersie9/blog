__author__ = 'vpersie9'
from flask import Blueprint

index=Blueprint('index', __name__)

from . import view,errors
from ..models import Permission

@index.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)