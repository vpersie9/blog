__author__ = 'vpersie9'
#-*-coding:utf8-*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
from flask import render_template,request,redirect,url_for,abort,flash,current_app,make_response
from flask.ext.login import login_required,current_user
from flask.ext.sqlalchemy import get_debug_queries
from werkzeug import secure_filename
import Image
import os
from . import index
from forms import EditProfileForm,EditProfileAdminForm,PostForm,CommentForm,Change_avatar
from ..models import User,Permission,Post,Comment
from ..decorators import admin_required,permission_required
from app import create_app
app=create_app('default')

@index.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['FACTORY_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response

@index.route('/wendy',methods=['POST','GET'])
def show():
    post_form=PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and \
        post_form.validate_on_submit():
        post=Post(title=post_form.title.data,body=post_form.body.data,author=current_user._get_current_object())
        post.save()
        return redirect(url_for('index.show'))
    page=request.args.get('page',1,type=int)
    show_followed=False
    if current_user.is_authenticated:
        show_followed=bool(request.cookies.get('show_followed',''))
    if show_followed:
        query=current_user.followed_posts
    else:
        query=Post.query
    pagination=query.order_by(Post.timestamp.desc()).paginate(
        page,per_page=current_app.config['FACTORY_POSTS_PER_PAGE'],error_out=False)
    posts=pagination.items
    return render_template('show.html',post_form=post_form,posts=posts,show_followed=show_followed,pagination=pagination)

@index.route('/all')
@login_required
def show_all():
    resp=make_response(redirect(url_for('index.show')))
    resp.set_cookie('show_followed','',max_age=30*24*60*60)
    return resp

@index.route('/followed')
@login_required
def show_followed():
    resp=make_response(redirect(url_for('index.show')))
    resp.set_cookie('show_followed','1',max_age=30*24*60*60)
    return resp

@index.route('/user/<username>')
def user(username):
    user=User.search(username=username)
    if user is None:
        abort(404)
    posts=user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html',user=user,posts=posts)

@index.route('/post/<int:id>', methods=['POST','GET'])
def post(id):
    # get 和 get_or_404() 都是用来获得主键信息的方法
    post=Post.query.get_or_404(id)
    comment_form=CommentForm()
    if comment_form.validate_on_submit():
        comment=Comment(body=comment_form.body.data,post=post,author=current_user._get_current_object())
        comment.save()
        # flash(u'评论成功')
        return redirect(url_for('index.post',id=post.id,page=-1))
    page=request.args.get('page',1,type=int)
    if page==-1:
        page=(post.comments.count()-1)/current_app.config['FACTORY_POSTS_PER_PAGE'] + 1
    pagination=post.comments.order_by(Comment.timestamp.asc()).paginate(
        page,per_page=current_app.config['FACTORY_POSTS_PER_PAGE'],error_out=False)
    comments=pagination.items
    return render_template('post.html',posts=[post],comment_form=comment_form,
                           comments=comments,pagination=pagination)

@index.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page=request.args.get('page',1,type=int)
    pagination=Comment.query.order_by(Comment.timestamp.asc()).paginate(
        page,per_page=current_app.config['FACTORY_POSTS_PER_PAGE'],error_out=False)
    comments=pagination.items
    return render_template('moderate.html',comments=comments,pagination=pagination,page=page)

@index.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment=Comment.query.get_or_404(id)
    comment.disabled=False
    comment.save()
    return redirect(url_for('index.moderate',page=request.args.get('page',1,type=int)))

@index.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment=Comment.query.get_or_404(id)
    comment.disabled=True
    comment.save()
    return redirect(url_for('index.moderate',page=request.args.get('page',1,type=int)))

@index.route('/edit/<int:id>',methods=['POST','GET'])
@login_required
def edit(id):
    post=Post.query.get_or_404(id)
    if current_user != post.author and not current_user.can(Permission.ADMINISTER):
        abort(403)
    edit_form=PostForm()
    if edit_form.validate_on_submit():
        post.title=edit_form.title.data
        post.body=edit_form.body.data
        post.save()
        # flash(u'您的博文已经编辑提交')
        return redirect(url_for("index.post",id=post.id))
    edit_form.title.data=post.title
    edit_form.body.data=post.body
    return render_template("edit_post.html",edit_form=edit_form)

@index.route('/edit-profile',methods=['POST','GET'])
@login_required
def edit_profile():
    edit_profile_form=EditProfileForm()
    if edit_profile_form.validate_on_submit():
        current_user.name=edit_profile_form.name.data
        current_user.location=edit_profile_form.location.data
        current_user.about_me=edit_profile_form.about_me.data
        current_user.save()
        # flash(u'您的资料信息已经更新完毕')
        return redirect(url_for('index.user',username=current_user.username))
    edit_profile_form.name.data=current_user.name
    edit_profile_form.location.data=current_user.location
    edit_profile_form.about_me.data=current_user.about_me
    return render_template('edit_profile.html',edit_profile_form=edit_profile_form,user=current_user)

@index.route('/edit-profile/<int:id>',methods=['POST','GET'])
@login_required
@admin_required
def edit_profile_admin(id):
    # get 和 get_or_404() 都是用来获得主键信息的方法
    user=User.query.get_or_404(id)
    edit_profile_form=EditProfileAdminForm(user=user)
    if edit_profile_form.validate_on_submit():
        u'''自我感觉如果更换邮箱会改变管理员的角色和权限
        因为管理员角色确定是根据config 的admin邮箱来判定的
        所以我打算暂时不定义邮箱和用户名和角色等表段'''
        # user.email=edit_profile_admin_form.email.data
        # user.username=edit_profile_admin_form.username.data
        # user.confirmed=edit_profile_admin_form.confirmed.data
        # user.role=Role.query.get(edit_profile_admin_form.role.data)
        user.name=edit_profile_form.name.data
        user.location=edit_profile_form.location.data
        user.about_me=edit_profile_form.about_me.data
        user.save()
        # flash(u'你的资料已经提交更新')
        return redirect(url_for('index.user',username=user.username))
    edit_profile_form.email.data=user.email
    edit_profile_form.username.data=user.username
    edit_profile_form.confirmed.data=user.confirmed
    edit_profile_form.name.data=user.name
    edit_profile_form.location.data=user.location
    edit_profile_form.about_me.data=user.about_me
    return render_template('edit_profile.html',edit_profile_form=edit_profile_form,user=user)

@index.route('/follow/<username>')
@login_required
def follow(username):
    user=User.query.filter_by(username=username).first()
    if user is None:
        # flash(u'用户不存在')
        return redirect(url_for('index.show'))
    if current_user.is_following(user):
        # flash(u'您已经关注了该用户')
        return redirect(url_for('index.user',username=username))
    current_user.follow(user)
    # flash(u'您关注了%s.' % username)
    return redirect(url_for('index.user',username=username))

@index.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user=User.query.filter_by(username=username).first()
    if user is None:
        # flash(u'用户不存在')
        return redirect(url_for('index.show'))
    current_user.unfollow(user)
    # flash(u'您取消了对%s的关注.' % username)
    return redirect(url_for('index.user',username=username))

@index.route('/followers/<username>')
# @login_required
def followers(username):
    if current_user.is_authenticated:
        user=User.query.filter_by(username=username).first()
        if user is None:
            # flash(u'该用户不存在')
            return redirect(url_for('index.show'))
        page=request.args.get('page',1,type=int)
        pagination=user.followers.paginate(page,per_page=current_app.config['FACTORY_POSTS_PER_PAGE'],error_out=False)
        follows=[{'user' : item.follower, 'timestamp' : item.timestamp} for item in pagination.items]
        return render_template('followers.html',user=user,endpoint='index.followers',pagination=pagination,follows=follows)
    else:
        return redirect(url_for('auth.login'))
@index.route('/followed_by/<username>')
# @login_required
def followed_by(username):
    if current_user.is_authenticated:
        user=User.query.filter_by(username=username).first()
        if user is None:
            # flash(u'该用户不存在')
            return redirect(url_for('index.show'))
        page=request.args.get('page',1,type=int)
        pagination=user.followed.paginate(page,per_page=current_app.config['FACTORY_POSTS_PER_PAGE'],error_out=False)
        follows=[{'user' : item.followed, 'timestamp' : item.timestamp} for item in pagination.items]
        return render_template('followers.html',user=user,endpoint='index.followed_by',pagination=pagination,follows=follows)
    else:
        return redirect(url_for('auth.login'))

@index.route('/posts-top')
def posts_top():
    posts_=Post.query.all()
    posts1=[]
    comments_list=[each for each in reversed(sorted([post.comments.count() for post in posts_]))]
    if len(posts_)>=20:
        comments_list=comments_list[:20]
    for number in comments_list:
        for post in posts_:
            if post.comments.count()==number:
                posts1.append(post)
    posts=list(set(posts1))
    u'列表保持原来的序列  因为集合是无序的'
    posts.sort(key=posts1.index)
    return render_template("posts_top.html",posts=posts)

@index.route('/users-top')
def users_top():
    users_1=User.query.all()
    users_=[]
    for each in users_1:
        if each.username is not None:
            users_.append(each)
    users1=[]
    followers_list=[each for each in reversed(sorted([user.followers.count() for user in users_]))]
    if len(users_)>=10:
        followers_list=followers_list[:10]
    for number in followers_list:
        for user in users_:
            if user.followers.count()==number:
                users1.append(user)
    users=list(set(users1))
    users.sort(key=users1.index)
    return render_template("users_top.html",users=users)

@index.route('/change_avatar',methods=['POST','GET'])
@login_required
def change_avatar():
    change_avatar_form=Change_avatar()
    if change_avatar_form.validate_on_submit():
        file=request.files['file']
        if file and '.' in file.filename and\
                        file.filename.split('.',1)[1] in app.config['ALLOWED_EXTENSIONS']:
            filename=secure_filename(file.filename)
            image=Image.open(file)
            image=[image.resize((256,256)),image.resize((60,60)),image.resize((23,23))]
            image[0].save(os.path.join(app.config['UPLOAD_FOLDER'].get('0'),filename))
            image[1].save(os.path.join(app.config['UPLOAD_FOLDER'].get('1'),filename))
            image[2].save(os.path.join(app.config['UPLOAD_FOLDER'].get('2'),filename))
            current_user.file_img=filename
            current_user.save()
            return redirect(url_for('index.edit_profile'))
    return render_template("change_avatar.html",change_avatar_form=change_avatar_form)