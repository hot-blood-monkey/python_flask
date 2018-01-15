import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    FLASKY_MAIL_SENDER = 'Flasky Admin <zhoudahoa@gmail.com>'
    FLASKY_ADMIN = '290322402@qq.com'

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_SERVER = 'smtp.googlemail.com'

    SQLALCHEMY_TRACK_MODIFICATIONS=True   #自己加的

    #新改的
    SSL_DISABLE = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLCLCHEMY_RECORD_QUERIES = True
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    # MAIL_PORT = 587
    # MAIL_USE_TLS = True
    MAIL_USERNAME = 'zhoudahoa@gmail.com'
    MAIL_PASSWORD = 'zhou1995'
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    FLASKY_MAIL_SENDER = 'Flasky Admin <flasky@example.com>'
    FLASKY_ADMIN = '290322402@qq.com' or 'zhuohao_hunan@163.com'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or "mysql+pymysql://root:123456@localhost:3306/test"


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or "mysql+pymysql://root:123456@localhost:3306/test"


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or "mysql+pymysql://root:123456@localhost:3306/test"


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

