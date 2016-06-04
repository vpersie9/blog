__author__ = 'vpersie9'
#-*-coding:utf8-*-
from wtforms import StringField,TextAreaField,SubmitField,BooleanField,SelectField,FileField
from flask.ext.wtf import Form
from wtforms.validators import Length,required
from flask.ext.pagedown.fields import PageDownField
from ..models import User,Role
import re

class EditProfileForm(Form):
    name=StringField(u"姓名", validators=[Length(0,64)])
    location=StringField(u"地址",validators=[Length(0,64)])
    about_me=TextAreaField(u"自我介绍")
    submit=SubmitField(u"更新资料")

class EditProfileAdminForm(Form):
    email=StringField(u'邮件',validators=[required(),Length(1,64)])
    username=StringField(u'用户名',validators=[required(),Length(1,64)])
    confirmed=BooleanField(u'审核')
    role=SelectField(u'角色',coerce=int)
    name=StringField(u"姓名", validators=[Length(0,64)])
    location=StringField(u"地址",validators=[Length(0,64)])
    about_me=TextAreaField(u"自我介绍")
    submit=SubmitField(u"更新资料")

    def __init__(self,user,*args,**kwargs):
        super(EditProfileAdminForm,self).__init__(*args,**kwargs)
        self.role.choices=[(role.id,role.name) for role in Role.query.order_by(Role.name).all()]
        self.user=user

class PostForm(Form):
    title=StringField(u'文章标题？',validators=[required()])
    body=PageDownField(u"文章内容？",validators=[required()])
    submit=SubmitField(u"发布文章")

class CommentForm(Form):
    body=StringField(u'发表您的评论',validators=[required()])
    submit=SubmitField(u'评论')

class Change_avatar(Form):
    file=FileField(u'选择上传图片',validators=[required()])
    submit=SubmitField(u'上传')