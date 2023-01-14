'''
Get some statistcs on the data
'''

from flask import Flask
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

import argparse

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
    print ("\n\n", '-'*25, "STATS", '-'*25, "\n\n")

    
    # get the number of users
    num_users = User.query.count()
    print(f'Number of users: {num_users}')

    # get the number of annotations - speaker is not None
    num_annotations = AnnotationEntry.query.filter(AnnotationEntry.speaker != None).count()
    print(f'Number of annotations: {num_annotations}')

    # get the number of verifications
    num_verifications = VerificationEntry.query.count()
    print(f'Number of verifications: {num_verifications}')

    print ("\n\n", '-'*50, "\n\n")

    # Get the number of annotations per user - get email addresses
    user_ids = [user.id for user in User.query.all()]
    user_emails = [user.username for user in User.query.all()]
    for user_id, user_email in zip(user_ids, user_emails):
        num_annotations = AnnotationEntry.query.filter_by(speaker=user_id).count()
        print(f'User {user_email} has {num_annotations} annotations')

    print ("\n\n", '-'*50, "\n\n")

    # Get the number of verifications per user - get email addresses
    user_ids = [user.id for user in User.query.all()]
    user_emails = [user.username for user in User.query.all()]
    for user_id, user_email in zip(user_ids, user_emails):
        num_verifications = VerificationEntry.query.filter_by(verifier_id=user_id).count()
        print(f'User {user_email} has {num_verifications} verifications')

    print ("\n\n", '-'*50, "\n\n")

    # How many missing annotations ?
    num_missing_annotations = AnnotationEntry.query.filter(AnnotationEntry.speaker == None).count()
    total_annotations = AnnotationEntry.query.count()
    print(f'Number of missing annotations: {num_missing_annotations} out of {total_annotations}')
