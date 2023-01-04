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

from datetime import datetime
import librosa
import soundfile as sf


'''
---------------------------------------------------
    Parsing command line arguments 
---------------------------------------------------
'''

import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=12345, help="Port to run the server on", required=False)
    parser.add_argument("--audio_folder", type=str, default="audio_files/", help="Path to the audio files", required=False)
    parser.add_argument("--run_over_https", default=False, help="Run over https", required=False, action='store_true')
    parser.add_argument("--debug", default=False, help="Run in debug mode", required=False, action='store_true')

    parser.add_argument("--users_table_name", type=str, default="users", help="Name of the table containing the users", required=False)
    parser.add_argument("--dataset_table_name", type=str, default="superb", help="Name of the table for storing the data", required=False)
    parser.add_argument("--verification_table_name", type=str, default="verifications", help="Name of the table containing the verifications", required=False)
    parser.add_argument("--database_name", type=str, default="database", help="Name of the database", required=False)
    return parser.parse_args()

args = parse_args()

'''
---------------------------------------------------
    Instantiating Flask app and SQLAlchemy
---------------------------------------------------
'''

app = Flask(__name__, static_url_path='/audio_files/', static_folder='audio_files/')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{args.database_name}.db'
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
    __tablename__ = args.users_table_name
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

# class for the database
class AnnotationEntry(db.Model):
    __tablename__ = args.dataset_table_name
    id = db.Column(db.Integer, primary_key=True)
    partition = db.Column(db.String(50), unique=False, nullable=False)
    utt = db.Column(db.String(50), unique=False, nullable=False)
    path = db.Column(db.String(50), unique=True, nullable=True)
    speaker = db.Column(db.Integer, unique=False, nullable=True)
    device = db.Column(db.String(50), unique=False, nullable=True)
    environment = db.Column(db.String(50), unique=False, nullable=True)
    verification_score = db.Column(db.Integer, unique=False, nullable=True)
    annotation_timestamp = db.Column(db.String(50), unique=False, nullable=True)

class VerificationEntry(db.Model):
    __tablename__ = args.verification_table_name
    id = db.Column(db.Integer, primary_key=True)
    utt_id = db.Column(db.Integer, unique=False, nullable=False)
    verifier_id = db.Column(db.Integer, unique=False, nullable=False)
    score = db.Column(db.Integer, unique=False, nullable=False)
    verification_timestamp = db.Column(db.String(50), unique=False, nullable=False)

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

@app.context_processor
def inject_template_scope():
    injections = dict()

    def cookies_check():
        value = request.cookies.get('cookie_consent')
        return value == 'true'
    injections.update(cookies_check=cookies_check)

    return injections

@app.route("/login", methods=['GET', 'POST'])
def login():
    '''
    Login route for flask-login
    '''
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
    '''
    Logout route for flask-login
    '''
    logout_user()
    return redirect(url_for('home'))

@app.route("/dashboard", methods=['GET', 'POST'])
@login_required
def dashboard():
    '''
    This is the main dashboard where the user lands after logging in
    '''
    # query the database for the current user
    user = User.query.filter_by(username=current_user.username).first()
    user_name = user.username
    user_id = user.id

    # get the number of annotations the user has done
    # query the superb table for the number of rows with the speaker = user_id
    num_annotations = AnnotationEntry.query.filter_by(speaker=user_id).count()

    return render_template("dashboard.html", username=user_name, num_annotations=num_annotations)

@app.route("/annotation", methods=['GET', 'POST'])
@login_required
def annotation():
    '''
    This function is called when the user clicks on the "Start Annotation" button
    It retrieve one random utterance from the database and displays it to the user
    to be annotated with his/her voice.
    '''
    # query the database for the current user
    user = User.query.filter_by(username=current_user.username).first()
    user_name = user.username
    user_id = user.id

    # Get some data for statistics
    #num_annotations = AnnotationEntry.query.filter(AnnotationEntry.speaker!=None).count()
    num_annotations = AnnotationEntry.query.filter_by(speaker=user_id).count()
    dataset_size = AnnotationEntry.query.count()

    if num_annotations == dataset_size:
        return render_template("done.html")

    # get the next utterance to annotate, random example not the first one
    next_utt = random.choice(AnnotationEntry.query.filter_by(speaker=None).all())
    
    utt_id = next_utt.id
    utt_text = next_utt.utt

    return render_template(
        "annotation.html", 
        username=user_name, 
        num_annotations=num_annotations, 
        #dataset_size=dataset_size, 
        utt_id=utt_id, 
        utt_text=utt_text,
        device = request.cookies.get('device'),
        environment = request.cookies.get('environment'),
    )


def convert_to_wav(file, filename):
    # command = ['ffmpeg', '-y', '-i', file, '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000', filename]
    command = ['ffmpeg', '-y', '-i', file, '-ar', '16000', filename]
    subprocess.run(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE)

@app.route("/submit", methods=['GET', 'POST'])
@login_required
def submit():
    '''
    This function is called when the user submits an annotation.
    It stores the information on the database updating the corresponding entry.
    '''

    audio_file = request.files.get("file")
    utt_id = request.form.get("utt_id")
    device = request.form.get("device")
    environment = request.form.get("environment")

    print (f"Device: {device} - Environment: {environment}")

    extension = request.form.get("mimeType").split("/")[-1]

    if extension == "aac":
        extension = "m4a"
    

    webm_filename = f"{args.audio_folder}/{utt_id}." + extension
    wav_filename  = f"{args.audio_folder}/{utt_id}.wav"
    audio_file.save(webm_filename)
    # use librosa to convert to wav
    # open the file with librosa
    y, sr = librosa.load(webm_filename, sr=16000)
    # save the file with soundfile
    sf.write(wav_filename, y, sr)


    #convert_to_wav(webm_filename, filename=wav_filename)

    # query the database for the current user
    user = User.query.filter_by(username=current_user.username).first()
    speaker_id = user.id

    # update the database
    utt = AnnotationEntry.query.filter_by(id=utt_id).first()
    utt.speaker = speaker_id
    utt.path = wav_filename
    utt.device = device
    utt.environment = environment
    utt.annotation_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.session.commit()

    data = {'message': 'Done', 'code': 'SUCCESS'}
    response = make_response(jsonify(data), 201) 
    response.set_cookie('device', device)
    response.set_cookie('environment', environment)

    return response


@app.route("/verification", methods=['GET', 'POST'])
@login_required
def verification():
    '''
    This function is called when the user clicks on the "Start Verification" button.
    It retrieve one of the utterances that have been annotated (with lowest verification_score)
    and displays it to the user for verification.

    The user can either accept or reject the annotation.
    '''
    # query the database for the current user
    user = User.query.filter_by(username=current_user.username).first()
    user_name = user.username
    user_id = user.id

    # Get random utterance to verify
    possible_utterances = AnnotationEntry.query.filter(AnnotationEntry.speaker!=None, AnnotationEntry.verification_score == 0).all()
    if len(possible_utterances) == 0:
        # if no utterance is "not verified" or with a score of 0, then choose a random one
        possible_utterances = AnnotationEntry.query.filter(AnnotationEntry.speaker!=None).all()

    if len(possible_utterances) == 0:
        # if no utterance available, then goes to the done page
        return render_template("done.html")

    next_utt = random.choice(possible_utterances)
    utt_id = next_utt.id
    utt_text = next_utt.utt
    utt_path = next_utt.path
    prev_verification_score = next_utt.verification_score

    return render_template(
        "verification.html", 
        username=user_name, 
        utt_id=utt_id, 
        utt_text=utt_text,
        utt_path=utt_path,
        prev_verification_score=prev_verification_score,
    )

@app.route("/verify", methods=['GET', 'POST'])
@login_required
def verify():
    '''
    This function is called when the user submits a verification.
    It stores the information on the database updating the corresponding entry.
    '''

    user = User.query.filter_by(username=current_user.username).first()
    user_name = user.username
    user_id = user.id

    utt_id = request.form.get("utt_id")
    evaluation = request.form.get("evaluation")

    # update the database
    utt = AnnotationEntry.query.filter_by(id=utt_id).first()

    if evaluation == "positive":
        utt.verification_score += 1
    else:
        utt.verification_score -= 1

    # insert entry in the verification table
    verification_entry = VerificationEntry(
        utt_id = utt_id,
        verifier_id = user_id,
        score = 1 if evaluation == "positive" else -1,
        verification_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    db.session.add(verification_entry)

    db.session.commit()

    data = {'message': 'Done', 'code': 'SUCCESS'}
    response = make_response(jsonify(data), 201) 
    return response

@app.route("/terms", methods=['GET', 'POST'])
def terms():
    return render_template("terms.html")

@app.route("/privacy", methods=['GET', 'POST'])
def privacy():
    return render_template("privacy.html")

@app.route("/tutorial", methods=['GET', 'POST'])
def privacy():
    return render_template("privacy.html")


'''
---------------------------------------------------
    Running the app
---------------------------------------------------
'''
if __name__ == "__main__":
    if args.run_over_https:
        app.run(port=args.port, debug=args.debug, ssl_context='adhoc', host="0.0.0.0")
    else:
        app.run(debug=args.debug, port=args.port, host="0.0.0.0")
