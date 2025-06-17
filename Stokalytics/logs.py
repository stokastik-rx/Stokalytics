from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class SessionRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    location = db.Column(db.String(120))
    type = db.Column(db.String(50))
    stakes = db.Column(db.String(50))
    time_in = db.Column(db.Time)
    time_out = db.Column(db.Time)
    money_in = db.Column(db.Float)
    money_out = db.Column(db.Float)
    comps_in = db.Column(db.Float)
    comps_out = db.Column(db.Float)
    tips = db.Column(db.Float)

