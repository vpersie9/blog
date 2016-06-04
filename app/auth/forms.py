__author__ = 'vpersie9'
#-*-coding:utf8-*-
from wtforms import StringField,PasswordField,BooleanField,SubmitField
from wtforms.validators import required,Length
from flask.ext.wtf import Form
from ..models import User
import re

class LoginForm(Form):
    email=StringField(u'登录邮箱:',validators=[required(),Length(1,64)])
    password=PasswordField(u'登录密码:',validators=[required()])
    remember_me=BooleanField(u'记住登录状态')
    submit=SubmitField(u'登录')

class RegisterForm(Form):
    username=StringField(u'用户名:',validators=[required(),Length(1,64)])
    email=StringField(u'邮箱:',validators=[required(),Length(1,64)])
    password=PasswordField(u'密码:',validators=[required()])
    password2=PasswordField(u'确认密码:',validators=[required()])
    submit=SubmitField(u'注册')

class Confirm_register(object):
    def registered_test(self,**kwargs):
        return User.search(**kwargs)

    def password_same_test(self,passwd,passwd2):
        return passwd==passwd2

    def email_css(self,email):
        return bool(len(email)>7) and re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email)

class Change_Passwd_Form(Form):
    old_password=PasswordField(u'当前密码:',validators=[required(),Length(1,64)])
    new_password=PasswordField(u'新密码:',validators=[required(),Length(1,64)])
    new_password2=PasswordField(u'确认密码:',validators=[required(),Length(1,64)])
    submit=SubmitField(u'确认修改')

class Recreate_Passwd_Form(Form):
    email=StringField(u'您的注册邮箱?',validators=[required(),Length(1,64)])
    submit=SubmitField(u'发送邮件')

class Confirm_Recreate_Passwd_Form(Form):
    password=PasswordField(u'您的新密码',validators=[required(),Length(1,64)])
    password2=PasswordField(u'确认密码',validators=[required(),Length(1,64)])
    submit=SubmitField(u'确认重置')

class Change_Email_Form(Form):
    password=PasswordField(u'用户密码：',validators=[required(),Length(1,64)])
    new_email=StringField(u'新的邮箱：',validators=[required(),Length(1,64)])
    submit=SubmitField(u'确认修改')

    def email_css(self,email):
        return bool(len(email)>7) and re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email)