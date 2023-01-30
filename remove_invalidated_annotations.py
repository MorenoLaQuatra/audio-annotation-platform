'''
Get some statistcs on the data
'''

from flask import Flask
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

import os

import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--users_table_name", type=str, default="users", help="Name of the table containing the users", required=False)
    parser.add_argument("--dataset_table_name", type=str, default="superb", help="Name of the table for storing the data", required=False)
    parser.add_argument("--verification_table_name", type=str, default="verifications", help="Name of the table containing the verifications", required=False)
    parser.add_argument("--database_name", type=str, default="database", help="Name of the database", required=False)
    return parser.parse_args()

args = parse_args()



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{args.database_name}.db'
app.config['SECRET_KEY'] = 'secret-key-goes-here'
db = SQLAlchemy(app)

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

with app.app_context():
    # reset all annotations that contains a verification score < 0

    # get all the annotations that have a verification score < 0
    invalid_annotations = AnnotationEntry.query.filter(AnnotationEntry.verification_score < 0).all()

    # get all the verifications that are associated with the invalid annotations
    invalid_verifications = VerificationEntry.query.filter(VerificationEntry.utt_id.in_([annotation.id for annotation in invalid_annotations])).all()

    # delete the verifications
    for verification in invalid_verifications:
        db.session.delete(verification)

    # get all the paths that are associated with the invalid annotations
    invalid_paths = [annotation.path for annotation in invalid_annotations]

    # reset the AnnotationEntry
    for annotation in invalid_annotations:
        annotation.path = None
        annotation.speaker = None
        annotation.device = None
        annotation.environment = None
        annotation.verification_score = 0
        annotation.annotation_timestamp = None

    # commit the changes
    db.session.commit()

    # get the number of annotations that have a verification score < 0
    print(f"Number of annotations that have a verification score < 0: {len(invalid_annotations)}")

    # remove all files in invalid_paths
    removed_files = 0
    for path in invalid_paths:
        wav_path = path
        mp4_path = path.replace(".wav", ".mp4")
        webm_path = path.replace(".wav", ".webm")

        if os.path.exists(wav_path):
            os.remove(wav_path)
            removed_files += 1

        if os.path.exists(mp4_path):
            os.remove(mp4_path)
            removed_files += 1

        if os.path.exists(webm_path):
            os.remove(webm_path)
            removed_files += 1

    print(f"Removed {removed_files} files")


