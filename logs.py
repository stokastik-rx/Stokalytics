
from datetime import datetime


from users import db



def parse_time(t_str):
    try:
        return datetime.strptime(t_str, "%H:%M").time() if t_str else None
    except ValueError:
        print(f"Invalid time format: {t_str}")
        return None





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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class BankRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class LedgerRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    account = db.Column(db.String(120), nullable=False)      # Bank name
    withdrawal = db.Column(db.Float, default=0.0)
    deposit = db.Column(db.Float, default=0.0)
    venture = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class CompRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    location = db.Column(db.String(120))
    type = db.Column(db.String(50))
    value = db.Column(db.Float)
    item = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class GiftRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    location = db.Column(db.String(120))
    type = db.Column(db.String(50))
    value = db.Column(db.Float)
    item = db.Column(db.String(25))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class LocationRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    color = db.Column(db.String(7), nullable=False)  # HEX color
    note = db.Column(db.Text, default="")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class LedSessRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    type = db.Column(db.String(120))
    value = db.Column(db.Float)
    cumulative = db.Column(db.Float)  # <-- ADD THIS LINE
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class LocationNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('location_record.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    location = db.relationship('LocationRecord', backref=db.backref('notes', lazy=True, cascade='all, delete-orphan'))


class BlackjackSpread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    value = db.Column(db.String(50), nullable=False)

class BlackjackGameRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    value = db.Column(db.String(100), nullable=False)


class BlackjackSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session_record.id'), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    spread = db.Column(db.String(50))
    game_speed = db.Column(db.String(5))
    game_rules = db.Column(db.String(100))
    system = db.Column(db.String(50))
    # Relationship to session
    session = db.relationship('SessionRecord', backref=db.backref('blackjack_session', uselist=False))

