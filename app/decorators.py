__author__ = 'vpersie9'
#-*-coding:utf8-*-
from functools import wraps
from flask import abort
from flask.ext.login import current_user
from models import Permission

u'''
使用python functools 标准库 自定义权限装饰器
permission_required 和 admin_required(后者可由前者得出)
'''
def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorator_function(*args,**kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args,**kwargs)
        return decorator_function
    return decorator

def admin_required(f):
    return permission_required(Permission.ADMINISTER)(f)