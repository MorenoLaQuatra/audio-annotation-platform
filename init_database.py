# parse MASSIVE data in json format and store it in a database

import argparse
import json
import os
import sys
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from flask import Flask
from flask_login import UserMixin

from tqdm import tqdm

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_path", type=str, default=None, help="Path to the data", required=True)
    parser.add_argument("--users_table_name", type=str, default="users", help="Name of the table for storing the data", required=True)
    parser.add_argument("--dataset_table_name", type=str, default="superb", help="Name of the table for storing the data", required=True)
    parser.add_argument("--verification_table_name", type=str, default="verifications", help="Name of the table for storing the data", required=True)
    parser.add_argument("--database_name", type=str, default="database", help="Name of the table for storing the data", required=True)
    return parser.parse_args()

args = parse_args()

# read dataset
dataset = pd.read_json(path_or_buf=args.data_path, lines=True)

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

# create table
with app.app_context():

    for table_name in [args.dataset_table_name, args.users_table_name, args.verification_table_name]:
        print("Do you want to remove the table {}?".format(table_name))
        print("Type 'yes' to confirm")
        confirmation = input()
        if confirmation == 'yes':
            db.session.execute(f'DROP TABLE IF EXISTS {table_name};')  
            db.session.commit()
            print(f"Table {table_name} removed")
        else:
            print(f"Table {table_name} not removed and dataset {args.data_path} not parsed")
            print("Exiting...")
            sys.exit()
    
    db.create_all()

    # insert data into table
    for index, row in tqdm(dataset.iterrows()):
        id = row['id']
        partition = row['partition']
        utt = row['utt']
        example = AnnotationEntry(id=id, partition=partition, utt=utt, verification_score=0)
        db.session.add(example)
        db.session.commit()
