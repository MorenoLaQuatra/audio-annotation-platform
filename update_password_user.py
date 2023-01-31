from flask import Flask
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", type=str, default=None, help="Username for the database", required=True)
    parser.add_argument("--password", type=str, default=None, help="Password for the database", required=True)
    parser.add_argument("--users_table_name", type=str, default="users", help="Name of the table for storing the data", required=False)
    return parser.parse_args()

args = parse_args()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
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

if args.username is not None and args.password is not None:
    with app.app_context():
        hashed_password = Bcrypt().generate_password_hash(args.password).decode('utf-8')
        # get the user with the username
        user = User.query.filter_by(username=args.username).first()
        # update the password
        user.password = hashed_password
        # update the database
        db.session.commit()
        print("User password updated in database")
        