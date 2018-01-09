from flask import Flask,render_template,session,redirect,url_for,flash
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from wtforms import StringField,SubmitField
from wtforms.validators import DataRequired

# app = Flask(__name__)
# app.config['SECRET_KEY']='ni cao'
# bootstrap=Bootstrap(app)

class NameForm(FlaskForm):
    name=StringField('你的名字？',validators=[DataRequired()])
    submit=SubmitField('Submit')





