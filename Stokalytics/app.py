from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import pandas as pd
from logs import db, SessionRecord
from datetime import datetime, time


app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/')


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///uploads.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)


@app.route('/')
def dashboard():
        return render_template('dashboard.html')





#Imported Time Conversion
def parse_time(value):
    try:
        if pd.isna(value):
            return None
        if isinstance(value, str):
            return datetime.strptime(value.strip(), "%H:%M:%S").time()
        if isinstance(value, pd.Timestamp):
            return value.time()
        if isinstance(value, time):
            return value
        if isinstance(value, float) and 0 <= value < 1:
            # Excel float format
            total_seconds = int(value * 86400)
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return time(hours, minutes)
        return pd.to_datetime(value).time()
    except Exception as e:
        print("Time parse failed:", value, e)
        return None




#GPT Generated Table Logic

@app.route('/file_upload', methods=['POST'])
def file_upload():
    file = request.files['file']

    if file:
        df = pd.read_excel(file, header=1)   # assumes row 2 is the actual header
        df = df.iloc[:, 1:]                  # optional: remove first column
        df.index = df.index + 1  # ✅ shift index to start from 1
        
        table_html = df.to_html(classes="table")
        for _, row in df.iterrows():

            if pd.isna(row['Date']):
                continue  # skip empty rows

            try:
                record = SessionRecord(
                    date=pd.to_datetime(row['Date']).date() if pd.notna(row['Date']) else None,
                    location=row['Location'],
                    type=row['Type'],
                    stakes=row['Stakes'],
                    time_in=parse_time(row['Time In']),
                    time_out=parse_time(row['Time Out']),
                    money_in=float(row['Money In']) if pd.notna(row['Money In']) else 0,
                    money_out=float(row['Money Out']) if pd.notna(row['Money Out']) else 0,
                    comps_in=float(row['Comps In']) if pd.notna(row['Comps In']) else 0,
                    comps_out=float(row['Comps Out']) if pd.notna(row['Comps Out']) else 0,
                    tips=float(row['Tips']) if pd.notna(row['Tips']) else 0
                )






                db.session.add(record)
            except Exception as e:
                print(f"Row error: {e}")  # optional: log bad rows

        db.session.commit()

        return render_template('upload.html', table=df.to_html(classes="table table-bordered"))






# Clear Logs
@app.route('/clear_logs', methods=['POST'])
def clear_logs():
    SessionRecord.query.delete()  # delete all records
    db.session.commit()
    return redirect(url_for('view_logs'))




@app.route('/logs')
def view_logs():
     sessions = SessionRecord.query.all()
     return render_template('logs.html', sessions=sessions, datetime=datetime)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555, debug=True)
