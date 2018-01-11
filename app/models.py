import os
from . import db
from . import login_manager

from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin,login_required,AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app

# app.config['SQLALCHEMY_DATABASE_URI']="mysql+pymysql://root:123456@localhost:3306/test"
# app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

class Permission:
    FOLLOW  = 0x01
    COMMENT = 0X02
    WRITE_ARTICLES =0X04
    MODERATE_COMMENTS=0X08
    ADMINSTER = 0X80

class Role(db.Model):
    __tablename__='roles'
    id =db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(32),unique=True)
    default=db.Column(db.Boolean,default=False,index=True)
    permissions = db.Column(db.Integer)

    users=db.relationship('User',backref='role',lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles={
            'User' :  (Permission.FOLLOW |
                       Permission.COMMENT|
                       Permission.WRITE_ARTICLES,True),
            'Moderate':(Permission.FOLLOW |
                       Permission.COMMENT|
                       Permission.WRITE_ARTICLES|
                        Permission.MODERATE_COMMENTS,True),
            'Administrator':(0xff,False)
        }
        for r in roles:
            role=Role.query.filter_by(username=r).first()
            if role is None:
                role = Role(username=r)
            role.permissions=roles[r][0]
            db.session.add(role)
        db.session.commit()


class User(UserMixin,db.Model):
    __tablename__='users'
    id = db.Column(db.Integer, primary_key=True)
    email=db.Column(db.String(64),unique=True,index=True)
    username = db.Column(db.String(64), unique=True,index=True)
    password_hash=db.Column(db.String(128))
    confirmed = db.Column(db.Boolean,default=False)

    role_id=db.Column(db.Integer,db.ForeignKey('roles.id'))

    def __int__(self,**kwargs):
        super(User,self).__init__(**kwargs)
        if self.role is None:
            if self.email ==current_app.config['FLASKY_ADMIN']:
                self.role=Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True)

    def can(self,permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINSTER)



    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    @password.setter
    def password(self,password):
        self.password_hash=generate_password_hash(password)

    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True


class AnonymousUser(AnonymousUserMixin):
    def can(self,permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
