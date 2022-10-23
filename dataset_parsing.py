# parse SUPERB data in json format and store it in a database

import argparse
import json
import os
import sys
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from flask import Flask

from tqdm import tqdm

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_path", type=str, default=None, help="Path to the data", required=True)
    return parser.parse_args()

args = parse_args()

# read dataset
dataset = pd.read_json(path_or_buf=args.data_path, lines=True)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'secret-key-goes-here'
db = SQLAlchemy(app)

# class for the database
class SuperbExample(db.Model):
    __tablename__ = 'superb'
    id = db.Column(db.Integer, primary_key=True)
    partition = db.Column(db.String(50), unique=False, nullable=False)
    utt = db.Column(db.String(50), unique=False, nullable=False)
    path = db.Column(db.String(50), unique=True, nullable=True)
    speaker = db.Column(db.String(50), unique=False, nullable=True) # TODO: change to db.Integer

# create table
with app.app_context():
    # remove superb table if it already exists
    db.session.execute('DROP TABLE IF EXISTS superb')  
    
    db.create_all()


    # insert data into table
    for index, row in tqdm(dataset.iterrows()):
        id = row['id']
        partition = row['partition']
        utt = row['utt']
        example = SuperbExample(id=id, partition=partition, utt=utt)
        db.session.add(example)
        db.session.commit()
