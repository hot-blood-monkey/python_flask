from flask import Flask,render_template,session,redirect,url_for,flash
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from flask_pagedown.fields import PageDownField
from wtforms import StringField,SubmitField,SelectField,TextAreaField,BooleanField
from wtforms.validators import DataRequired,Length,Email,Regexp,ValidationError
from ..models import Role,User

# app = Flask(__name__)
# app.config['SECRET_KEY']='ni cao'
# bootstrap=Bootstrap(app)

class NameForm(FlaskForm):
    name=StringField('你的名字？',validators=[DataRequired()])
    submit=SubmitField('Submit')


class EditProfileForm(FlaskForm):
    name =StringField('Real name',validators=[Length(0,64)])
    location=StringField('Location',validators=[Length(0,64)])
    about_me= TextAreaField('About me')
    submit = SubmitField('提交')



class EditProfileAdminForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(0, 64), Email()])

    username = StringField('Username', validators=[DataRequired(), Length(0, 64),
                                                   Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, '用户名必须是文字，数字，点，或者下划线')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    name =StringField('Real name',validators=[Length(0,64)])
    location=StringField('Location',validators=[Length(0,64)])
    about_me = TextAreaField('About me')

    submit=SubmitField('提交')

    def __init__(self,user,*args,**kwargs):
        super(EditProfileAdminForm,self).__init__(*args,*kwargs)
        self.role.choices=[(role.id,role.username) for role in Role.query.order_by(Role.username).all()]
        self.user = user

    def validate_email(self,field):
        if field.data !=self.user.email and User.query.filter_by(username=field.data).first():
            raise ValidationError('邮箱已经注册')

    def validate_username(self,field):
        if field.data!=self.username and User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已经存在')

class PostForm(FlaskForm):
    body = PageDownField('记录下你的idea，或许它会惊艳世界',validators=[DataRequired()])  #把原来的多行文本框变成了markdown富文本`
    submit = SubmitField('提交')

class CommentForm(FlaskForm):  #评论的表单
    body = StringField('',validators=[DataRequired()])
    submit = SubmitField('提交')



