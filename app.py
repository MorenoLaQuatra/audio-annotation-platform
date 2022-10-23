'''
Simple Flask app that is used for annotating data using speech.
It allows user login using flask-login
'''

import subprocess
import random

from flask import Flask
from flask import render_template, url_for, redirect, request, make_response, jsonify

from flask_sqlalchemy import SQLAlchemy

from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user

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
    parser.add_argument("--audio_folder", type=str, default="audio_files/", help="Path to the audio files", required=True)
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
    # TODO: Add more fields here

# class for the database
class SuperbExample(db.Model):
    __tablename__ = 'superb'
    id = db.Column(db.Integer, primary_key=True)
    partition = db.Column(db.String(50), unique=False, nullable=False)
    utt = db.Column(db.String(50), unique=False, nullable=False)
    path = db.Column(db.String(50), unique=True, nullable=True)
    speaker = db.Column(db.String(50), unique=False, nullable=True) #TODO: change to db.Integer

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

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/dashboard", methods=['GET', 'POST'])
@login_required
def dashboard():
    # query the database for the current user
    user = User.query.filter_by(username=current_user.username).first()
    user_name = user.username
    user_id = user.id

    # get the number of annotations the user has done
    # query the superb table for the number of rows with the speaker = user_id
    num_annotations = SuperbExample.query.filter_by(speaker=user_id).count()

    return render_template("dashboard.html", username=user_name, num_annotations=num_annotations)

@app.route("/annotation", methods=['GET', 'POST'])
@login_required
def annotation():
    # query the database for the current user
    user = User.query.filter_by(username=current_user.username).first()
    user_name = user.username
    user_id = user.id

    # Get some data for statistics
    num_annotations = SuperbExample.query.filter(SuperbExample.speaker!=None).count()
    dataset_size = SuperbExample.query.count()

    # get the next utterance to annotate, random example not the first one
    next_utt = random.choice(SuperbExample.query.filter_by(speaker=None).all())
    
    utt_id = next_utt.id
    utt_text = next_utt.utt

    return render_template(
        "annotation.html", 
        username=user_name, 
        num_annotations=num_annotations, 
        dataset_size=dataset_size, 
        utt_id=utt_id, 
        utt_text=utt_text
    )

def convert_webm_to_wav(file, filename):
    command = ['ffmpeg', '-y', '-i', file, '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000', filename]
    subprocess.run(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE)

@app.route("/submit", methods=['GET', 'POST'])
@login_required
def submit():

    audio_file = request.files.get("file")
    utt_id = request.form.get("utt_id")

    webm_filename = f"{ARGS.audio_folder}/{utt_id}.webm"
    wav_filename  = f"{ARGS.audio_folder}/{utt_id}.wav"
    audio_file.save(webm_filename)
    convert_webm_to_wav(webm_filename, filename=wav_filename)

    # query the database for the current user
    user = User.query.filter_by(username=current_user.username).first()
    speaker_id = user.id

    # update the database
    utt = SuperbExample.query.filter_by(id=utt_id).first()
    utt.speaker = speaker_id
    utt.path = wav_filename
    db.session.commit()

    data = {'message': 'Done', 'code': 'SUCCESS'}
    response = make_response(jsonify(data), 201) 

    return response

'''
---------------------------------------------------
    Running the app
---------------------------------------------------
'''
if __name__ == "__main__":
    app.run(debug=True, port=ARGS.port)
