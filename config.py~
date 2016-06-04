__author__ = 'vpersie9'
class Config(object):

    SECRET_KEY='z\xe7\x14\x0b\xdf*7|#\xbdPU:\xfb\x03\x0bWR\xb3_\xeb,'
    SQLALCHEMY_COMMIT_ON_TEARDOWN=True
    SQLALCHEMY_TRACK_MODIFICATIONS=True
    FACTORY_MAIL_SUBJECT_PREFIX='[Factory]'
    FACTORY_MAIL_SENDER='Factory Admin <zengxiang7@163.com>'
    FACTORY_ADMIN='zengxiang7@163.com'
    FACTORY_POSTS_PER_PAGE = 20
    FACTORY_SLOW_DB_QUERY_TIME = 0.5
    SQLALCHEMY_RECORD_QUERIES = True
    UPLOAD_FOLDER={
        '0':'/home/vpersie9/PycharmProjects/flask_factory/app/static/img0',
        '1':'/home/vpersie9/PycharmProjects/flask_factory/app/static/img1',
        '2':'/home/vpersie9/PycharmProjects/flask_factory/app/static/img2'
    }
    ALLOWED_EXTENSIONS=set(['jpg','jpeg','JPG','png','gif'])
    MAX_CONTENT_LENGTH=4*1024*1024

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG=True
    MAIL_SERVER='smtp.163.com'
    MAIL_PORT=465
    MAIL_USE_TLS=False
    MAIL_USE_SSL=True
    MAIL_USERNAME='zengxiang7@163.com'
    MAIL_PASSWORD='xiang521jing'
    SQLALCHEMY_DATABASE_URI="mysql://root:199099@localhost/develop?charset=utf8"

class TestingConfig(Config):
    TESTING=True
    SQLALCHEMY_DATABASE_URI="mysql://root:199099@localhost/test?charset=utf8"

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI="mysql://root:199099@localhost/production?charset=utf8"

config={
    'development':DevelopmentConfig,
    'testing':TestingConfig,
    'production':ProductionConfig,

    'default':DevelopmentConfig
}