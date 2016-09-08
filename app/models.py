__author__ = 'vpersie9'
#-*-coding:utf8-*-
from . import db,login_manager
from .exceptions import ValidationError
from werkzeug.security import generate_password_hash,check_password_hash
from flask.ext.login import UserMixin,AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app,url_for
from datetime import datetime
import hashlib
from markdown import markdown
import bleach
import sys
reload(sys)
sys.setdefaultencoding('utf8')


class Permission(object):
    FOLLOW=0x01
    COMMENT=0x02
    WRITE_ARTICLES=0x04
    MODERATE_COMMENTS=0x08
    ADMINISTER=0x80

class Role(db.Model):
    __tablename__='roles'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(64),unique=True)
    default=db.Column(db.Boolean,default=False,index=True)
    permissions=db.Column(db.Integer)
    users=db.relationship('User',backref='role',lazy='dynamic')

    u'''
    insert_roles()函数并不直接创建新角色的对象,而是通过角色查找现有的角色,然后进行更新.只有当数据库中
    没有某个角色名时才会创建新的角色对象.如果以后更新了角色列表,就可以执行更新操作了.要想添加新角色,
    或者修改角色的权限,修改roles 数组,再运行函数即可.注意,“匿名”角色不需要在数据库中表示出来,这个角色
    的作用就是为了表示不在数据库中的用户.
    '''
    @staticmethod
    def insert_roles():
        roles={
            'User':(Permission.FOLLOW |
                    Permission.COMMENT |
                    Permission.WRITE_ARTICLES,True),
            'Moderator':(Permission.FOLLOW |
                         Permission.COMMENT |
                         Permission.WRITE_ARTICLES |
                         Permission.MODERATE_COMMENTS,False),
            'Administrator':(0xff,False)

        }
        for i in roles:
            role=Role.query.filter_by(name=i).first()
            if role is None:
                role=Role(name=i)
            role.permissions=roles[i][0]
            role.default=roles[i][1]
            db.session.add(role)
        db.session.commit()

    def __init__(self,name):
        self.name=name

    def __repr__(self):
        return self.name

class Post(db.Model):
    __tablename__='posts'
    id=db.Column(db.Integer,primary_key=True)
    title=db.Column(db.Text)
    body=db.Column(db.Text)
    timestamp=db.Column(db.DateTime,index=True,default=datetime.utcnow)
    author_id=db.Column(db.Integer,db.ForeignKey('users.id'))
    body_html=db.Column(db.Text)
    comments=db.relationship('Comment',backref='post',lazy='dynamic')

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self.id
        except Exception,e:
            db.session.rollback()
            return e
        finally:
            return 1


    def to_json(self):
        json_post={
            'url':url_for('api.get_post',id=self.id,_external=True),
            'title':self.title,
            'body':self.body,
            'body_html':self.body_html,
            'timestamp':self.timestamp,
            'author':url_for('api.get_user',id=self.author_id,_external=True),
            'comments':url_for('api.get_post_comments',id=self.id,_external=True),
            'comment_count':self.comments.count()
        }
        return json_post

    @staticmethod
    def from_json(json_post):
        title=json_post.get('title')
        body=json_post.get('body')
        if title is None or title=='':
            raise ValidationError(u'文章标题为空')
        if body is None or body=='':
            raise ValidationError(u'文章内容为空')
        return Post(title=title,body=body)

    @staticmethod
    def on_changed_body(target,value,oldvalue,initiator):
        allowed_tags=['a','abbr','acronym','b','blockquote','code','em',
                      'i','li','ol','pre','strong','ul','h1','h2','h3','p','img0']
        target.body_html=bleach.linkify(bleach.clean(markdown(value,output_format='html'),
                                                     tags=allowed_tags,strip=True))
db.event.listen(Post.body,'set',Post.on_changed_body)

class Follow(db.Model):
    __tablename__='follows'
    follower_id=db.Column(db.Integer,db.ForeignKey('users.id'),primary_key=True)
    followed_id=db.Column(db.Integer,db.ForeignKey('users.id'),primary_key=True)
    timestamp=db.Column(db.DateTime,default=datetime.utcnow)

class Comment(db.Model):
    __tablename__='comments'
    id=db.Column(db.Integer,primary_key=True)
    body=db.Column(db.Text)
    body_html=db.Column(db.Text)
    timestamp=db.Column(db.DateTime,index=True,default=datetime.utcnow)
    disabled=db.Column(db.Boolean)
    author_id=db.Column(db.Integer,db.ForeignKey('users.id'))
    post_id=db.Column(db.Integer,db.ForeignKey('posts.id'),index=True)

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self.id
        except Exception,e:
            db.session.rollback()
            return e
        finally:
            return 1

    @staticmethod
    def on_changed_body(target,value,oldvalue,initiator):
        allowed_tags=['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i', 'strong']
        target.body_html=bleach.linkify(bleach.clean(markdown(value,output_format='html'),
                                                     tags=allowed_tags,strip=True))

    def to_json(self):
        json_comment = {
            'url': url_for('api.get_comment', id=self.id, _external=True),
            'post': url_for('api.get_post', id=self.post_id, _external=True),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author': url_for('api.get_user', id=self.author_id,
                              _external=True),
        }
        return json_comment

    @staticmethod
    def from_json(json_comment):
        body = json_comment.get('body')
        if body is None or body == '':
            raise ValidationError('comment does not have a body')
        return Comment(body=body)


db.event.listen(Comment.body,'set',Comment.on_changed_body)

class User(UserMixin,db.Model):
    __tablename__='users'
    id=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String(64),unique=True,index=True)
    username=db.Column(db.String(64),unique=True,index=True)
    password_hash=db.Column(db.String(128))
    confirmed=db.Column(db.Boolean,default=False)
    role_id=db.Column(db.Integer,db.ForeignKey('roles.id'))
    posts=db.relationship('Post',backref='author',lazy='dynamic')
    comments=db.relationship('Comment',backref='author',lazy='dynamic')
    name=db.Column(db.String(64))
    location=db.Column(db.String(64))
    about_me=db.Column(db.Text())
    member_since=db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen=db.Column(db.DateTime(),default=datetime.utcnow)
    avatar_hash=db.Column(db.String(128))
    file_img=db.Column(db.String(128))
    followed=db.relationship('Follow',
                             foreign_keys=[Follow.follower_id],
                             backref=db.backref('follower',lazy='joined'),
                             lazy='dynamic',
                             cascade='all,delete-orphan')
    followers=db.relationship('Follow',
                              foreign_keys=[Follow.followed_id],
                              backref=db.backref('followed',lazy='joined'),
                              lazy='dynamic',
                              cascade='all,delete-orphan')

    def __init__(self,**kwargs):
            super(User,self).__init__(**kwargs)
            if self.role is None:
                if self.email==current_app.config['FACTORY_ADMIN']:
                    self.role=Role.query.filter_by(permissions=0xff).first()
                if self.role is None:
                    self.role=Role.query.filter_by(default=True).first()
            if self.email is not None and self.avatar_hash is None:
                self.avatar_hash=hashlib.md5(
                    self.email.encode('utf-8')).hexdigest()
            self.followed.append(Follow(followed=self))

    u'''重头戏: 下面介绍了属性装饰器的 获取和设置password
    User类中的password参数通过类的实例化之后作为属性将值传递给password_push'''
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self,password_content):
        self.password_hash=generate_password_hash(password_content)

    def verify_password(self,password_text):
        return check_password_hash(self.password_hash,password_text)

    def __repr__(self):
        return self.username

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self.id
        except Exception,e:
            db.session.rollback()
            return e
        finally:
            return 1

    def ping(self):
        self.last_seen=datetime.utcnow()
        self.save()

    def change_avat(self):
        pass

    def can(self,permissions):
        return self.role is not None and \
               (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    @staticmethod
    def search(**kwargs):
        try:
            return User.query.filter_by(**kwargs).first()
        except Exception,e:
            return e

    def generate_confirmation_token(self,expiration=3600):
        s=Serializer(current_app.config['SECRET_KEY'],expiration)
        return s.dumps({'confirm':self.id})

    def confirm(self,token):
        s=Serializer(current_app.config['SECRET_KEY'])
        try:
            data=s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed=True
        self.save()
        return True

    def generate_change_token(self, param, expiration=3600):
        s=Serializer(current_app.config['SECRET_KEY'],expiration)
        return s.dumps({'change':param})

    def confirm_change(self,token):
        s=Serializer(current_app.config['SECRET_KEY'])
        try:
            data=s.loads(token)
        except:
            return False
        return data.get('change')

    def gravatar(self,size=100,default='identicon',rating='g'):
        url='https://secure.gravatar.com/avatar'
        hash=self.avatar_hash or hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.\
            format(url=url,hash=hash,size=size,default=default,rating=rating)

    def follow(self,user):
        if not self.is_following(user):
            f=Follow(follower=self,followed=user)
            db.session.add(f)
            db.session.commit()

    def unfollow(self,user):
        f=self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)
            db.session.commit()

    def is_following(self,user):
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self,user):
        return self.followers.filter_by(follower_id=user.id).first() is not None

    @property
    def followed_posts(self):
        return Post.query.join(Follow,Follow.followed_id==Post.author_id).filter(
            Follow.follower_id==self.id)

    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    def generate_auth_token(self,expiration):
        s=Serializer(current_app.config['SECRET_KEY'],expires_in=expiration)
        return s.dumps({'id':self.id})

    @staticmethod
    def verify_auth_token(token):
        s=Serializer(current_app.config['SECRET_KEY'])
        try:
            data=s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    def to_json(self):
        json_user={
            'url':url_for('api.get_post',id=self.id,_external=True),
            'username':self.username,
            'member_since':self.member_since,
            'last_seen':self.last_seen,
            'posts':url_for('api.get_user_posts',id=self.id,_external=True),
            'followed_posts':url_for('api.get_user_followed_posts',id=self.id,_external=True),
            'post_count':self.posts.count()
        }
        return json_user

u'''
加载用户的回调函数 这个是登录用户能够直接调用current_user实现机制???  好像是user.id 就可以指向这个用户的信息
'''
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

u'''
这个对象继承自Flask-Login中的AnonymousUserMixin类,并将其设为用户未登录时
current_user的值.这样程序不用先检查用户是否登录,就能自由调用current_user.can()
和current_user.is_administrator().
'''

class AnonymousUser(AnonymousUserMixin):

    def can(self,permissions):
        return False and permissions

    def is_administrator(self):
        return False
u'''
加载匿名用户的回调函数 这个是匿名用户能够直接调用current_user.can/is_administrator的实现机制
'''
login_manager.anonymous_user=AnonymousUser

