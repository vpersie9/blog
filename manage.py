__author__='vpersie9'
#-*-coding:utf8-*-
from flask.ext.script import Manager,Shell,Server
from app import create_app,db
from app.models import User,Role,Post,Permission
from flask.ext.migrate import Migrate,MigrateCommand

app=create_app('default')
manager=Manager(app)
migrate=Migrate(app,db)

def test():

    u"""测试"""
    import unittest
    tests=unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

u'make_context 回调函数'
def make_shell_text():
    return dict(app=app,db=db,User=User,Role=Role,test=test,Post=Post,Permission=Permission)

manager.add_command("shell",Shell(make_context=make_shell_text))
manager.add_command('db',MigrateCommand)
manager.add_command('runserver',Server(port=8090))

u'下面的注释函数能够实现和回调函数中的test相同的功能'
@manager.command
def test():
    """
    Run this test.
    """
    import unittest
    tests=unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

@manager.command
def profile(length=25, profile_dir=None):
    u"""在请求分析器的监视下运行程序"""
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length],
                                      profile_dir=profile_dir)
    app.run()


@manager.command
def deploy():
    u"""运行deployment."""
    from flask.ext.migrate import upgrade
    from app.models import Role, User

    u'更新数据库'
    upgrade()

    u'更新用户角色'
    Role.insert_roles()

    u'将自己设定为关注着'
    User.add_self_follows()

if __name__=="__main__":
    manager.run()