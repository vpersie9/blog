__author__ = 'vpersie9'
#-*-coding:utf8-*-
from flask import render_template,request,redirect,url_for,flash
from flask.ext.login import login_user,logout_user,login_required,current_user
from . import auth
from .forms import LoginForm,RegisterForm,Confirm_register,Change_Passwd_Form,\
    Recreate_Passwd_Form,Confirm_Recreate_Passwd_Form,Change_Email_Form
from ..models import User
from ..email import sender_mail
import hashlib

u'下面的两个路由用来过滤已经登录但是尚未激活确认的用户 并最终将其定向到未确认路由'
@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed and request.endpoint[:5] != 'auth.':
            return redirect(url_for('auth.unconfirmed'))

u'匿名用户和已经激活确认的用户直接定向到主界面路由'
@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('index.show'))
    return render_template('auth/unconfirmed.html')

@auth.route('/login',methods=['POST','GET'])
def login():
    login_form=LoginForm()
    if login_form.validate_on_submit():
        email=login_form.email.data
        password=login_form.password.data
        remember_me=login_form.remember_me.data
        submit=login_form.submit.data
        user=User.search(email=email)
        if user and user.verify_password(password):
            login_user(user,remember_me,submit)
            return redirect(request.args.get('next') or url_for('index.show'))
        flash(u'邮箱或密码不正确')
        return redirect(url_for('auth.login'))
    return render_template("auth/login.html",login_form=login_form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash(u'您已经成功注销登录')
    return redirect(url_for('auth.login'))

@auth.route('/register',methods=['POST','GET'])
def register():
    register_form=RegisterForm()
    confirm=Confirm_register()
    if register_form.validate_on_submit():
        username=register_form.username.data
        email=register_form.email.data
        password=register_form.password.data
        password2=register_form.password2.data
        if not confirm.email_css(email):
            flash(u'请输入正确的邮箱格式 如example@xxx.com')
            return redirect(url_for('auth.register'))
        if confirm.registered_test(username=username):
            flash(u'该用户名已经被注册')
            return redirect(url_for('auth.register'))
        if confirm.registered_test(email=email):
            flash(u'该邮箱已经被注册')
            return redirect(url_for('auth.register'))
        if not confirm.password_same_test(password,password2):
            flash(u'前后密码不一致')
            return redirect(url_for('auth.register'))
        else:
            user=User(email=email,username=username,password=password)
            user.save()
            token=user.generate_confirmation_token()
            sender_mail(user.email,u'请确认注册账户','auth/email/confirm',user=user,token=token)
            flash(u'注册成功 请登录邮箱完成验证激活')
            return redirect(url_for('auth.login'))
    return render_template('auth/register.html', register_form=register_form)

u'''
这里面有一个问题 必须保证登录之后才可以点击激活帐户
如果没有登录就直接激活会引发一个异常
所以@login_required 要重新考虑
所以现在考虑使用current_user.is_authenticated 来检测用户的登录情况 确保登录的用户可以点击链接激活
'''
@auth.route('/confirm/<token>')
# @login_required
def confirm(token):
    if current_user.is_authenticated:
        if current_user.confirmed:
            return redirect(url_for('index.show'))
        if current_user.confirm(token):
            flash(u'您已验证激活成功')
        else:
            flash(u'验证激活失败或验证链接已经过期')
        return redirect(url_for('auth.login'))
    flash(u'请在激活链接之前 先登录用户')
    return redirect(url_for('auth.login'))

@auth.route('/confirm')
@login_required
def resend_confirmation():
    token=current_user.generate_confirmation_token()
    sender_mail(current_user.email,u'请确认注册账户','auth/email/confirm',user=current_user,token=token)
    flash(u'新的验证链接已经发送到您邮箱 请登录邮箱完成验证激活')
    return redirect(url_for('auth.login'))

u'程序还需要加入的工作是  修改密码  通过邮箱重置密码  还有修改电子邮箱地址'

@auth.route('/chgpasswd',methods=['POST','GET'])
@login_required
def change_passwd():
    change_passwd_form=Change_Passwd_Form()
    if change_passwd_form.validate_on_submit():
        old_password=change_passwd_form.old_password.data
        new_password=change_passwd_form.new_password.data
        new_password2=change_passwd_form.new_password2.data
        if not current_user.verify_password(old_password):
            flash(u'原始密码输入错误请重新输入')
            return redirect(url_for('auth.change_passwd'))
        if new_password != new_password2:
            flash(u'重置密码前后输入不一致 请重新输入')
            return redirect(url_for('auth.change_passwd'))
        else:
            current_user.password=new_password
            current_user.save()
            return redirect(url_for('index.show'))
    return render_template('auth/chgpasswd.html',change_passwd_form=change_passwd_form)

@auth.route('/repasswd',methods=['POST','GET'])
def recreate_passwd():
    recreate_passwd_form=Recreate_Passwd_Form()
    if recreate_passwd_form.validate_on_submit():
        email=recreate_passwd_form.email.data
        user=User.search(email=email)
        if user:
            token=user.generate_change_token(email)
            sender_mail(user.email,u'重置登录密码','auth/email/recreate_pwd',user=user,token=token)
            flash(u'邮件已发送 请登录邮箱激活重置')
    return render_template('auth/repasswd.html',recreate_passwd_form=recreate_passwd_form)

@auth.route('/confirm_pwd/<token>',methods=['POST','GET'])
def confirm_recreate_pwd(token):
    confirm_recreate_pwd_form=Confirm_Recreate_Passwd_Form(request.form)
    if confirm_recreate_pwd_form.validate_on_submit():
        password=confirm_recreate_pwd_form.password.data
        password2=confirm_recreate_pwd_form.password2.data
        user=User.search(email=User().confirm_change(token))
        if password != password2:
            flash(u'前后密码输不一致 请重新输入')
            return redirect(url_for('auth.confirm_recreate_pwd',token=token))
        else:
            user.password=password
            user.save()
            flash(u'密码重置成功')
            return redirect(url_for('auth.login'))
    return render_template('auth/confirm_repasswd.html',confirm_recreate_pwd_form=confirm_recreate_pwd_form)

@auth.route('/change_email',methods=['POST','GET'])
@login_required
def change_email():
    change_email_form=Change_Email_Form()
    if change_email_form.validate_on_submit():
        password=change_email_form.password.data
        new_email=change_email_form.new_email.data
        if not current_user.verify_password(password):
            flash(u'密码错误 请重新输入!')
            return redirect(url_for('auth.change_email'))
        if not change_email_form.email_css(new_email):
            flash(u'请输入正确的邮箱格式 如example@xxx.com')
            return redirect(url_for('auth.change_email'))
        else:
            token=current_user.generate_change_token(new_email)
            sender_mail(new_email,u'修改注册邮箱','auth/email/change_email',user=current_user,token=token)
            flash(u'邮件已发送 请登录新的注册邮箱激活链接')
            return redirect(url_for('auth.change_email'))
    return render_template('auth/change_email.html',change_email_form=change_email_form)

@auth.route('/confirm_email/<token>')
@login_required
def confirm_email(token):
    if current_user.confirm_change(token):
        current_user.email=current_user.confirm_change(token)
        current_user.avatar_hash=hashlib.md5(current_user.email.encode('utf-8')).hexdigest()
        current_user.save()
        return redirect(url_for('index.show'))
    flash(u'注册邮箱修改失败 请重新修改')
    return redirect(url_for('auth.change_email'))
