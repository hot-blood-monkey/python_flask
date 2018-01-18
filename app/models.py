import os,hashlib
from datetime import datetime
from markdown import markdown
import bleach
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

class Follow(db.Model):
    __tablename__='follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True) #关注者
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)  #被关注者
    timestamp=db.Column(db.DateTime, default=datetime.utcnow)




class Post(db.Model):
    __tablename__= 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body=db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True,default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    body_html = db.Column(db.Text)

    @staticmethod
    def generate_fake(count=100):
        from random import seed,randint
        import forgery_py

        seed()
        user_count = User.query.count()

        for i in range(count):
            u=User.query.offset(randint(0,user_count - 1)).first()
            p=Post(
                body=forgery_py.lorem_ipsum.sentences(randint(1,3)),
                timestamp = forgery_py.date.date(True),
                author=u
            )

            db.session.add(p)
            db.session.commit()

    @staticmethod
    def on_changed_body(target,value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
                             markdown(value, output_format='html'),
                             tags=allowed_tags, strip=True ))

db.event.listen(Post.body,'set',Post.on_changed_body)


class Role(db.Model):
    __tablename__='roles'
    id =db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(32), unique=True)
    default=db.Column(db.Boolean,default=False, index=True)
    permissions = db.Column(db.Integer)

    users=db.relationship('User', backref='role', lazy='dynamic')

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

    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic', cascade='all,delete-orphan')
    followers = db.relationship('Follow',
                               foreign_keys=[Follow.followed_id],
                               backref=db.backref('followed', lazy='joined'),
                               lazy='dynamic', cascade='all,delete-orphan')


    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)  #确保父类初始化
        self.follows(self)  #用户注册就关注自己,这样就能实现打开关注者就能看到自己的文章
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(username='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()

    @staticmethod  #静态方法,添加自身为关注者
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id== Post.author_id).filter(Follow.follower_id==self.id)

    @staticmethod
    def generate_fake(count=100):
        from random import seed,randint
        import forgery_py

        seed()
        user_count =User.query.count()

        for i in range(count):
            u = User.query.offset(randint(0, user_count-1)).first()
            p=Post(body=forgery_py.lorem_ipsum.sentences(randint(1, 3)),
                   timestamp=forgery_py.date.date(True),
                   author=u
                   )
            db.session.add(p)
            db.session.commit()
    def follow(self,user):
        if not self.is_following(user):
            f=Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        f=self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self,user):
        return self.follow.filter_by(followers_id=user.id).first() is not None

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
