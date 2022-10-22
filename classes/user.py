from app import db, app

class User(db.Model, UserMixin):
    '''
    User class for flask-login
    '''
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)