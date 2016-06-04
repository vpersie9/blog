__author__ = 'vpersie9'
import random
from threading import Thread
from flask import render_template
from flask.ext.mail import Message
from app import create_app
from app import mail
app=create_app('default')

def send_async_email(app,msg):
    with app.app_context():
        mail.send(msg)

def sender_mail(to,subject,template,**kwargs):
    msg=Message(app.config['FACTORY_MAIL_SUBJECT_PREFIX']+subject,sender=app.config['FACTORY_MAIL_SENDER'],recipients=[to])
    msg.body=render_template(template+'.txt',**kwargs)
    msg.html=render_template(template+'.html',**kwargs)
    thr=Thread(target=send_async_email,args=[app,msg])
    thr.start()
    return thr