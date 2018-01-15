import os,hashlib
from datetime import datetime
from . import db
from . import login_manager
from config import config

from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin,AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app,request


class Permission:
    FOLLOW  = 0x01
    COMMENT = 0X02
    WRITE_ARTICLES =0X04
    MODERATE_COMMENTS=0X08
    ADMINSTER = 0X80

class Post(db.Model):
    __tablename__= 'posts'
    id = db.Column(db.Integer,primary_key=True)
    body=db.Column(db.Text)
    timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
    author_id = db.Column(db.Integer,db.ForeignKey('users.id'))


class Role(db.Model):
    __tablename__='roles'
    id =db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(32),unique=True)
    default=db.Column(db.Boolean,default=False,index=True)
    permissions = db.Column(db.Integer)

    users=db.relationship('User',backref='role',lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

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
        default_role = 'Moderate'
        for r in roles:
            role = Role.query.filter_by(username=r).first()
            if role is None:
                role = Role(username=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.username == default_role)
            db.session.add(role)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def __repr__(self):
        return '<Role %r>' % self.username


class User(UserMixin,db.Model):
    __tablename__='users'
    id = db.Column(db.Integer, primary_key=True)
    email=db.Column(db.String(64),unique=True,index=True)
    username = db.Column(db.String(64), unique=True,index=True)
    password_hash=db.Column(db.String(128))
    confirmed = db.Column(db.Boolean,default=False)

    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)

    avatar_hash = db.Column(db.String(32))  #邮件头像的散列值存放处

    role_id=db.Column(db.Integer,db.ForeignKey('roles.id'))           #外部键

    posts = db.relationship('Post',backref='author',lazy='dynamic')  #外部键 的 对应部分

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(username='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()



    def ping(self):
        self.last_seen=datetime.utcnow()
        db.session.add(self)


    def can(self, permissions):
        return self.role is not None and ((self.role.permissions & int(permissions)) == int(permissions))

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

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps(
            {'change_email': self.id, 'new_email': new_email}).decode('utf-8')

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = self.gravatar_hash()
        db.session.add(self)
        return True

    # 添加邮箱的头像
    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()

    def gravatar(self,size=100,default='identicon',rating='g'):
    #gravatar（）会使用模型中保存的散列值
        if request.is_secure:
            url='http://secure.gravatar.com/avatar'
        else:
            url='http://www.gravatar.com/avatar'
        hash = self.gravatar_hash()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)


class AnonymousUser(AnonymousUserMixin):
    def can(self,permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
