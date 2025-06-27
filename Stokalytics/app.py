from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import pandas as pd
from logs import db, SessionRecord
from datetime import datetime, time
from logs import BankRecord
from collections import defaultdict



app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/')

app.jinja_env.globals['getattr'] = getattr

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///uploads.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

migrate = Migrate(app, db)



@app.route('/')
def dashboard():
    from collections import defaultdict
    from datetime import datetime
    from logs import SessionRecord, LedgerRecord, LedSessRecord

    # === Chart 1: Cumulative Profit (PnL vs Time) ===
    sessions = SessionRecord.query.order_by(SessionRecord.date, SessionRecord.time_in).all()

    cumulative_profit = 0
    cumulative_time = 0
    chart_point_map = {}

    for s in sessions:
        money_in = s.money_in or 0
        money_out = s.money_out or 0
        profit = money_out - money_in
        cumulative_profit += profit

        if s.time_in and s.time_out:
            duration = (datetime.combine(s.date, s.time_out) - datetime.combine(s.date, s.time_in)).total_seconds() / 3600
        else:
            duration = 0
        cumulative_time += duration

        time_key = round(cumulative_time, 2)
        chart_point_map[time_key] = round(cumulative_profit, 2)

    chart_points = [{"x": x, "y": y} for x, y in sorted(chart_point_map.items())]

    # === Sidebar filter: unique types ===
    unique_types = sorted(set(s.type for s in sessions if s.type))

    # === Chart 2: Total Bankroll by Date using LedSessRecord cumulative values ===
    ledsess_entries = LedSessRecord.query.order_by(LedSessRecord.date, LedSessRecord.id).all()

    cumulative = 0
    date_to_cumulative = {}

    for entry in ledsess_entries:
        cumulative += entry.value or 0
        date_str = entry.date.isoformat()
        date_to_cumulative[date_str] = cumulative  # always update to keep the last entry on that date

    combined_chart_data = [
        {"x": date_str, "y": round(cum_val, 2)}
        for date_str, cum_val in sorted(date_to_cumulative.items())
    ]

    return render_template(
        'dashboard.html',
        chart_data=chart_points,
        unique_types=unique_types,
        combined_chart_data=combined_chart_data
    )











#Imported Time Conversion
def parse_time(value):
    try:
        if pd.isna(value):
            return None
        if isinstance(value, str):
            value = value.strip()
            try:
                return datetime.strptime(value, "%H:%M:%S").time()
            except ValueError:
                return datetime.strptime(value, "%H:%M").time()
        if isinstance(value, pd.Timestamp):
            return value.time()
        if isinstance(value, time):
            return value
        if isinstance(value, float) and 0 <= value < 1:
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
        df.index = df.index + 1  # shift index to start from 1
        
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
        sync_ledsess()


        return render_template('upload.html', table=df.to_html(classes="table table-bordered"))






# Clear Logs
@app.route('/clear_logs', methods=['POST'])
def clear_logs():
    SessionRecord.query.delete()  # delete all records
    db.session.commit()
    return redirect(url_for('view_logs'))

@app.route('/delete_session/<int:id>', methods=['POST'])
def delete_session(id):
    session = SessionRecord.query.get_or_404(id)
    db.session.delete(session)
    db.session.commit()
    sync_ledsess()

    return redirect(url_for('view_logs'))



@app.route('/logs')
def view_logs():
     sessions = SessionRecord.query.all()
     return render_template('logs.html', sessions=sessions, datetime=datetime)

@app.route('/update_logs', methods=['POST'])
def update_logs():
    from sqlalchemy.orm.exc import NoResultFound
    i = 0
    while True:
        session_id = request.form.get(f'id_{i}')
        if not session_id:
            break
        session = SessionRecord.query.get(int(session_id))
        if not session:
            i += 1
            continue
        for field in ['date', 'location', 'type', 'stakes', 'time_in', 'time_out', 'money_in', 'money_out', 'comps_in', 'comps_out', 'tips']:
            val = request.form.get(f'{field}_{i}')
            if val:
                if field in ['money_in', 'money_out', 'comps_in', 'comps_out', 'tips']:
                    setattr(session, field, float(val))
                elif field in ['time_in', 'time_out']:
                    setattr(session, field, parse_time(val))
                elif field == 'date':
                    setattr(session, field, pd.to_datetime(val).date())
                else:
                    setattr(session, field, val)
        i += 1
    db.session.commit()
    sync_ledsess()

    return redirect(url_for('view_logs'))










from logs import LedgerRecord  # ensure LedgerRecord is imported
@app.route('/add_session', methods=['POST'])
def add_session():
    form = request.form

    try:
        new_session = SessionRecord(
            date=pd.to_datetime(form.get('date')).date() if form.get('date') else None,
            location=form.get('location'),
            type=form.get('type'),
            stakes=form.get('stakes'),
            time_in=parse_time(form.get('time_in')),
            time_out=parse_time(form.get('time_out')),
            money_in=float(form.get('money_in') or 0),
            money_out=float(form.get('money_out') or 0),
            comps_in=float(form.get('comps_in') or 0),
            comps_out=float(form.get('comps_out') or 0),
            tips=float(form.get('tips') or 0),
        )

        db.session.add(new_session)
        db.session.commit()
        sync_ledsess()

    except Exception as e:
        print("Error adding session:", e)

    return redirect(url_for('dashboard'))




@app.route('/banking')
def view_banking():
    sessions = SessionRecord.query.all()
    banks = BankRecord.query.order_by(BankRecord.name).all()
    ledger = LedgerRecord.query.order_by(LedgerRecord.date.desc()).all()

    unique_types = sorted(set(s.type for s in sessions if s.type).union(
                          set(l.venture for l in ledger if l.venture)))

    chart_data = {}
    bankroll_totals = {}

    for venture in unique_types:
        combined = []

        for s in sessions:
            if s.type == venture:
                combined.append({
                    "date": s.date,
                    "change": (s.money_out or 0) - (s.money_in or 0)
                })

        for l in ledger:
            if l.venture == venture:
                combined.append({
                    "date": l.date,
                    "change": (l.withdrawal or 0) - (l.deposit or 0)
                })

        # Sort and deduplicate by date, keeping max cumulative
        combined.sort(key=lambda x: x["date"])
        cumulative = 0
        date_to_cum = {}

        for item in combined:
            date_str = str(item["date"])
            cumulative += item["change"]
            if date_str not in date_to_cum or cumulative > date_to_cum[date_str]:
                date_to_cum[date_str] = round(cumulative, 2)

        sorted_points = sorted(date_to_cum.items())
        chart_points = [{"x": d, "y": y} for d, y in sorted_points]
        chart_data[venture] = chart_points

        if chart_points:
            bankroll_totals[venture] = chart_points[-1]["y"]
        else:
            bankroll_totals[venture] = 0

    # Net change per bank (deposits - withdrawals)
        bank_balances = defaultdict(float)

        for entry in ledger:
            bank_balances[entry.account] += (entry.deposit or 0) - (entry.withdrawal or 0)


    return render_template(
    'banking.html',
    sessions=sessions,
    banks=banks,
    unique_types=unique_types,
    ledger=ledger,
    ventureChartData=chart_data,
    bankroll_totals=bankroll_totals,
    bank_balances=bank_balances,
    datetime=datetime
)



@app.route('/add_bank', methods=['POST'])
def add_bank():
    name = request.form.get('bank_name')
    if name:
        new_bank = BankRecord(name=name.strip())
        db.session.add(new_bank)
        db.session.commit()
    return redirect(url_for('view_banking'))

@app.route('/delete_bank/<int:bank_id>', methods=['POST'])
def delete_bank(bank_id):
    bank = BankRecord.query.get(bank_id)
    if bank:
        db.session.delete(bank)
        db.session.commit()
    return redirect(url_for('view_banking'))



@app.route('/comps')
def view_comps():
    from sqlalchemy import func

    # Get self comps and gift comps
    self_comps = CompRecord.query.all()
    gift_comps = GiftRecord.query.all()

    # Combine into unified format
    all_comps = [
        {
            "date": c.date,
            "location": c.location,
            "type": c.type,
            "value": c.value,
            "item": c.item,
            "source": "Self Comp"
        } for c in self_comps
    ] + [
        {
            "date": g.date,
            "location": g.location,
            "type": g.type,
            "value": g.value,
            "item": g.item,
            "source": "Gift"
        } for g in gift_comps
    ]

    # Sort by date descending
    all_comps.sort(key=lambda x: x["date"] or "", reverse=True)

    # Grouped total by type for sidebar (optional)
    from collections import defaultdict
    summary = defaultdict(float)
    for c in all_comps:
        summary[c["type"]] += c["value"] or 0

    comp_summary = [{"type": k, "total": v} for k, v in summary.items()]

    return render_template("comps.html", comp_records=all_comps, comp_summary=comp_summary)



from logs import LedgerRecord

@app.route('/update-ledger', methods=['POST'])
def update_ledger():
    form = request.form

    try:
        new_entry = LedgerRecord(
            date=pd.to_datetime(form.get('date')).date(),
            account=form.get('account'),
            withdrawal=float(form.get('withdrawal') or 0),
            deposit=float(form.get('deposit') or 0),
            venture=form.get('venture')
        )
        db.session.add(new_entry)
        db.session.commit()
        sync_ledsess()

    except Exception as e:
        print("Error saving ledger entry:", e)

    return redirect(url_for('view_banking'))

@app.route('/ledger')
def view_ledger():
    ledger_entries = LedgerRecord.query.order_by(LedgerRecord.date.desc()).all()
    return render_template('ledger.html', ledger=ledger_entries)



@app.route('/edit-ledger/<int:ledger_id>', methods=['POST'])
def edit_ledger_entry(ledger_id):
    entry = LedgerRecord.query.get(ledger_id)
    if entry:
        form = request.form
        entry.date = pd.to_datetime(form.get('date')).date()
        entry.account = form.get('account')
        entry.venture = form.get('venture')
        amount = float(form.get('amount') or 0)
        if form.get('type') == 'deposit':
            entry.deposit = amount
            entry.withdrawal = 0
        else:
            entry.withdrawal = amount
            entry.deposit = 0
        db.session.commit()
    return redirect(url_for('view_banking'))

@app.route('/blackjack')
def view_blackjack():
    # Pull session records for blackjack
    session_rows = SessionRecord.query.filter_by(type='Blackjack').all()
    session_data = [
        {
            "date": s.date,
            "change": (s.money_out or 0) - (s.money_in or 0),
            "source": "session"
        }
        for s in session_rows
    ]

    # Pull ledger records for blackjack
    ledger_rows = LedgerRecord.query.filter_by(venture='Blackjack').all()
    ledger_data = [
        {
            "date": l.date,
            "change": (l.withdrawal or 0) - (l.deposit or 0),
            "source": "ledger"
        }
        for l in ledger_rows
    ]

    # Combine and sort by date
    all_data = session_data + ledger_data
    all_data.sort(key=lambda x: x["date"])

    return render_template('blackjack.html', records=all_data)

@app.route('/delete_ledger/<int:ledger_id>', methods=['POST'])
def delete_ledger(ledger_id):
    entry = LedgerRecord.query.get(ledger_id)
    if entry:
        db.session.delete(entry)
        db.session.commit()
    return redirect(url_for('view_banking'))








from logs import CompRecord  # ensure CompRecord is imported

@app.route('/log_comp', methods=['POST'])
def log_comp():
    form = request.form

    try:
        log_comp = CompRecord(
            date=pd.to_datetime(form.get('date')).date() if form.get('date') else None,
            location=form.get('location'),
            type=form.get('type'),
            value=form.get('value'),
            item=form.get('item'),
        )

        db.session.add(log_comp)
        db.session.commit()

    except Exception as e:
        print("Error logging comp:", e)

    return redirect(url_for('view_comps'))


from logs import GiftRecord  # ensure GiftRecord is imported

@app.route('/log_gift', methods=['POST'])
def log_gift():
    form = request.form

    try:
        log_gift = GiftRecord(
            date=pd.to_datetime(form.get('date')).date() if form.get('date') else None,
            location=form.get('location'),
            type=form.get('type'),
            value=form.get('value'),
            item=form.get('item'),
        )

        db.session.add(log_gift)
        db.session.commit()

    except Exception as e:
        print("Error logging gift:", e)

    return redirect(url_for('view_comps'))


from logs import LocationRecord  # add this at the top if not already imported

@app.route('/add_location', methods=['POST'])
def add_location():
    name = request.form.get('name')
    color = request.form.get('color')
    if name and color:
        new_location = LocationRecord(name=name.strip(), color=color, note="")
        db.session.add(new_location)
        db.session.commit()
    return redirect(url_for('view_locations'))

@app.route('/update_location_note/<int:location_id>', methods=['POST'])
def update_location_note(location_id):
    location = LocationRecord.query.get(location_id)
    if location:
        location.note = request.form.get('note') or ""
        db.session.commit()
    return redirect(url_for('view_locations'))

@app.route('/locations')
def view_locations():
    sessions = SessionRecord.query.all()
    locations = LocationRecord.query.all()  # assuming this is your model

    # Build summary per location
    summary = {}
    for loc in locations:
        loc_sessions = [s for s in sessions if s.location == loc.name]
        loc_summary = {
            'total_pl': 0,
            'total_hours': 0,
            'comps': 0,
            'Blackjack': {'pl': 0, 'hours': 0},
            'Poker': {'pl': 0, 'hours': 0},
            'Match Play': {'pl': 0, 'hours': 0}
        }

        for s in loc_sessions:
            profit = (s.money_out or 0) - (s.money_in or 0)
            duration = 0
            if s.time_in and s.time_out:
                duration = (datetime.combine(s.date, s.time_out) - datetime.combine(s.date, s.time_in)).total_seconds() / 3600

            loc_summary['total_pl'] += profit
            loc_summary['total_hours'] += duration
            loc_summary['comps'] += (s.comps_out or 0)

            if s.type in loc_summary:
                loc_summary[s.type]['pl'] += profit
                loc_summary[s.type]['hours'] += duration

        summary[loc.name] = loc_summary

    return render_template('locations.html', locations=locations, summary=summary)




def sync_ledsess():
    from logs import db, LedSessRecord, LedgerRecord, SessionRecord

    seen = {}

    # --- Step 1: Ledger entries ---
    for entry in LedgerRecord.query.all():
        if not entry.date or not entry.venture:
            continue

        delta = (entry.deposit or 0) - (entry.withdrawal or 0)
        if delta == 0:
            continue

        key = (entry.date, entry.account, round(-delta, 2))  # 👈 Flip sign here
        seen[key] = LedSessRecord(date=entry.date, type=entry.account, value=-delta)

    # --- Step 2: Session entries ---
    for sess in SessionRecord.query.all():
        if not sess.date or not sess.type:
            continue

        profit = (sess.money_out or 0) - (sess.money_in or 0)
        if profit == 0:
            continue

        key = (sess.date, sess.type, round(profit, 2))
        seen[key] = LedSessRecord(date=sess.date, type=sess.type, value=profit)

    # --- Step 3: Clear + add all unique values ---
    LedSessRecord.query.delete()
    db.session.bulk_save_objects(seen.values())
    db.session.commit()







from logs import LedSessRecord

@app.route('/ledsess')
def view_ledsess():
    entries = LedSessRecord.query.order_by(LedSessRecord.date, LedSessRecord.id).all()
    cumulative = 0
    rows = []

    for entry in entries:
        cumulative += entry.value or 0
        rows.append({
            "date": entry.date,
            "type": entry.type,
            "value": entry.value,
            "cumulative": round(cumulative, 2)
        })

    return render_template('ledsess.html', ledsess=rows)


@app.route('/refresh-ledsess', methods=['POST'])
def refresh_ledsess():
    sync_ledsess()
    return redirect(url_for('view_ledsess'))












if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555, debug=True)