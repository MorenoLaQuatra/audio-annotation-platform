'''
Simple Flask app that is used for annotating data using speech.
It allows user login using flask-login
'''

from flask import Flask
from flask import render_template, url_for, redirect

from flask_sqlalchemy import SQLAlchemy

from flask_login import LoginManager, UserMixin, login_user, login_required#, logout_user, current_user

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError

from flask_bcrypt import Bcrypt


'''
---------------------------------------------------
    Parsing command line arguments 
---------------------------------------------------
'''

import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=12345, help="Port to run the server on", required=False)
    return parser.parse_args()

ARGS = parse_args()

'''
---------------------------------------------------
    Instantiating Flask app and SQLAlchemy
---------------------------------------------------
'''

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'secret-key-goes-here'
db = SQLAlchemy(app)

'''
---------------------------------------------------
    Instantiating Flask-Login
---------------------------------------------------
'''

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


'''
---------------------------------------------------
    Creating classes for flask-login
---------------------------------------------------
'''

class User(db.Model, UserMixin):
    '''
    User class for flask-login
    '''
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

'''
class RegisterForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=50)], render_kw={"placeholder": "Username"})
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user_object = User.query.filter_by(username=username.data).first()
        if user_object:
            raise ValidationError('Username already exists. Please select a different username.')

'''

class LoginForm(FlaskForm):
    '''
    Login form for flask-login
    '''
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=50)], render_kw={"placeholder": "Username"})
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')

'''
---------------------------------------------------
    Defining routes
---------------------------------------------------
'''
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_object = User.query.filter_by(username=form.username.data).first()
        if user_object:
            if Bcrypt().check_password_hash(user_object.password, form.password.data):
                login_user(user_object)
                return redirect(url_for('dashboard'))
        return '<h1>Invalid username or password</h1>'
    return render_template("login.html", form=form)

@app.route("/dashboard", methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template("dashboard.html")

'''
---------------------------------------------------
    Running the app
---------------------------------------------------
'''
if __name__ == "__main__":
    app.run(debug=True, port=ARGS.port)
