from flask import Flask, render_template, request, redirect, url_for, current_app, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from datetime import datetime, time, date
import pandas as pd
from collections import defaultdict
import random

# --- Shared DB instance ---
from users import db, User
from logs import SessionRecord, BankRecord, LedgerRecord, CompRecord, GiftRecord, LocationRecord, LedSessRecord
from logs import LocationNote  # add LocationNote import
from logs import BlackjackSpread, BlackjackGameRule
from logs import BlackjackSession

# --- Helper: Generate random HEX color ---
def random_color():
    import random
    return "#" + ''.join(random.choices('0123456789ABCDEF', k=6))

# --- Flask App Setup ---
app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///uploads.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.jinja_env.globals['getattr'] = getattr  # useful for dynamic rendering

# --- Initialize DB & Migrations ---
db.init_app(app)
migrate = Migrate(app, db)

app.secret_key = 'your_super_secret_key_here'





# --- Login Manager Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # type: ignore # redirects unauthorized users to login page

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



@app.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/landing')
def landing_direct():
    return render_template('landing.html')

@app.route('/dashboard')
@login_required
def dashboard():
    from collections import defaultdict
    from datetime import datetime
    from logs import SessionRecord, LedSessRecord
    sync_ledsess()  # Always update LedSess before rendering dashboard

    print(f"\n=== DASHBOARD LOADED FOR USER {current_user.id} ===")

    # === Chart 1: Cumulative Profit (PnL vs Time) ===
    sessions = SessionRecord.query.filter_by(user_id=current_user.id).order_by(SessionRecord.date, SessionRecord.time_in).all()
    print(f"[dashboard] Found {len(sessions)} sessions for user {current_user.id}")
    
    cumulative_profit = 0
    cumulative_time = 0
    chart_point_map = {}
    
    for i, s in enumerate(sessions):
        money_in = s.money_in or 0
        money_out = s.money_out or 0
        profit = money_out - money_in
        cumulative_profit += profit
        
        if s.time_in and s.time_out:
            duration = (datetime.combine(s.date, s.time_out) - datetime.combine(s.date, s.time_in)).total_seconds() / 3600
        else:
            duration = 0
            
        cumulative_time += duration
        chart_point_map[round(cumulative_time, 2)] = round(cumulative_profit, 2)
        print(f"  Session {i+1}: {s.date} {s.type} - Money: ${money_in}→${money_out} (Profit: ${profit}) - Time: {duration:.2f}h - Cumulative: ${cumulative_profit:.2f}")
    
    chart_points = [{"x": x, "y": y} for x, y in sorted(chart_point_map.items())]
    print('[dashboard] Cumulative Profit chart_points:', chart_points)

    unique_types = sorted(set(s.type for s in sessions if s.type))
    print(f'[dashboard] Unique venture types: {unique_types}')

    # === Chart 2: Total Bankroll by Date (from LedSess) ===
    ledsess_entries = LedSessRecord.query.filter_by(user_id=current_user.id).order_by(LedSessRecord.date, LedSessRecord.id).all()
    print(f"[dashboard] Found {len(ledsess_entries)} LedSess entries for user {current_user.id}")
    
    cumulative = 0
    date_to_cumulative = {}
    
    for entry in ledsess_entries:
        cumulative += entry.value or 0
        date_str = entry.date.isoformat()
        date_to_cumulative[date_str] = cumulative
        print(f"  LedSess: {entry.date} {entry.type} ${entry.value:.2f} → Cumulative: ${cumulative:.2f}")
    
    combined_chart_data = [
        {"x": date, "y": round(val, 2)} for date, val in sorted(date_to_cumulative.items())
    ]
    print('[dashboard] Total Bankroll by Date combined_chart_data:', combined_chart_data)

    # === Chart 3: Venture Charts ===
    venture_chart_map = defaultdict(list)
    venture_cumulative = defaultdict(float)
    venture_elapsed_time = defaultdict(float)
    
    for s in sessions:
        venture = s.type or "Unknown"
        profit = (s.money_out or 0) - (s.money_in or 0)
        venture_cumulative[venture] += profit

        if venture in ("Poker", "Blackjack"):
            # Always use hours as x-axis for Poker/Blackjack
            if s.time_in and s.time_out:
                duration = (datetime.combine(s.date, s.time_out) - datetime.combine(s.date, s.time_in)).total_seconds() / 3600
                venture_elapsed_time[venture] += duration
                x_val = round(venture_elapsed_time[venture], 2)
            else:
                continue  # skip if no time info
        else:
            # For other ventures (e.g., Match Play), use date as x-axis
            if s.date:
                x_val = s.date.isoformat()
            else:
                continue

        venture_chart_map[venture].append({
            "x": x_val,
            "y": round(venture_cumulative[venture], 2)
        })
        print(f"  Venture {venture}: x={x_val}, y=${venture_cumulative[venture]:.2f}")
    
    venture_chart_data = dict(venture_chart_map)
    print('[dashboard] Venture chart data:', venture_chart_data)

    return render_template(
        'dashboard.html',
        chart_data=chart_points,
        unique_types=unique_types,
        combined_chart_data=combined_chart_data,
        venture_chart_data=venture_chart_data,
        game_preference=current_user.game_preference
    )



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        game_preference = request.form.get('game_preference', 'both')

        if User.query.filter_by(username=username).first():
            return "Username already exists"

        new_user = User(username=username, email=email, game_preference=game_preference)  # type: ignore
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('dashboard'))

    return render_template('signup.html')







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





@app.route('/file_upload', methods=['POST'])
@login_required
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
                record = SessionRecord(  # type: ignore
                    date=pd.to_datetime(row['Date']).date() if pd.notna(row['Date']) else None,  # type: ignore
                    location=row['Location'],  # type: ignore
                    type=row['Type'],  # type: ignore
                    stakes=row['Stakes'],  # type: ignore
                    time_in=parse_time(row['Time In']),  # type: ignore
                    time_out=parse_time(row['Time Out']),  # type: ignore
                    money_in=float(row['Money In']) if pd.notna(row['Money In']) else 0,  # type: ignore
                    money_out=float(row['Money Out']) if pd.notna(row['Money Out']) else 0,  # type: ignore
                    comps_in=float(row['Comps In']) if pd.notna(row['Comps In']) else 0,  # type: ignore
                    comps_out=float(row['Comps Out']) if pd.notna(row['Comps Out']) else 0,  # type: ignore
                    tips=float(row['Tips']) if pd.notna(row['Tips']) else 0,  # type: ignore
                    user_id=current_user.id  # type: ignore # ✅ secure the record
                )
                db.session.add(record)
            except Exception as e:
                print(f"Row error: {e}")  # optional: log bad rows

        db.session.commit()
        sync_ledsess()

        return render_template('upload.html', table=df.to_html(classes="table table-bordered"))








@app.route('/clear_logs', methods=['POST'])
@login_required
def clear_logs():
    SessionRecord.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return redirect(url_for('view_logs'))



@app.route('/delete_session/<int:id>', methods=['POST'])
@login_required
def delete_session(id):
    session = SessionRecord.query.get_or_404(id)

    if session.user_id != current_user.id:
        return "Unauthorized", 403

    db.session.delete(session)
    db.session.commit()
    sync_ledsess()

    return redirect(url_for('view_logs'))



@app.route('/logs')
@login_required
def view_logs():
    print("=== VIEW_LOGS CALLED ===")
    
    # Check if filtering by type
    session_type = request.args.get('type')
    
    if session_type:
        sessions = SessionRecord.query.filter_by(user_id=current_user.id, type=session_type).all()
        print(f"Found {len(sessions)} {session_type} sessions for user {current_user.id}")
    else:
        sessions = SessionRecord.query.filter_by(user_id=current_user.id).all()
        print(f"Found {len(sessions)} sessions for user {current_user.id}")
    
    # Build a mapping of location name to color
    locations = LocationRecord.query.filter_by(user_id=current_user.id).all()
    location_colors = {loc.name: loc.color for loc in locations}
    
    # Get blackjack session data if filtering by blackjack
    blackjack_sessions = {}
    if session_type == 'Blackjack':
        sync_blackjack_sessions()
        from logs import BlackjackSession
        bj_sessions = (
            db.session.query(SessionRecord, BlackjackSession)
            .join(BlackjackSession, BlackjackSession.session_id == SessionRecord.id)
            .filter(SessionRecord.user_id == current_user.id, SessionRecord.type == 'Blackjack')
            .all()
        )
        for s, bj in bj_sessions:
            blackjack_sessions[s.id] = {
                'spread': bj.spread or '',
                'game_speed': bj.game_speed or '',
                'game_rules': bj.game_rules or '',
                'system': bj.system or ''
            }
    
    return render_template('logs.html', 
                         sessions=sessions, 
                         datetime=datetime, 
                         location_colors=location_colors,
                         session_type=session_type,
                         blackjack_sessions=blackjack_sessions)




@app.route('/update_logs', methods=['POST'])
@login_required
def update_logs():
    from sqlalchemy.exc import NoResultFound
    # No debug imports or file logging
    
    # Get all session IDs from the form
    session_ids = [key.split('_')[1] for key in request.form if key.startswith('id_')]
    any_changes = False
    for session_id in session_ids:
        session = SessionRecord.query.get(int(session_id))
        if not session or session.user_id != current_user.id:
            continue
        session_changed = False
        for field in ['date', 'location', 'type', 'stakes', 'time_in', 'time_out', 'money_in', 'money_out', 'comps_in', 'comps_out', 'tips']:
            val = request.form.get(f'{field}_{session_id}')
            if val is not None and val != '':
                # Convert value based on field type
                if field in ['money_in', 'money_out', 'comps_in', 'comps_out', 'tips']:
                    try:
                        new_val = float(val) if val else 0
                        if getattr(session, field) != new_val:
                            setattr(session, field, new_val)
                            session_changed = True
                    except ValueError:
                        continue
                elif field in ['time_in', 'time_out']:
                    new_val = parse_time(val)
                    if getattr(session, field) != new_val:
                        setattr(session, field, new_val)
                        session_changed = True
                elif field == 'date':
                    try:
                        new_val = pd.to_datetime(val).date() if val else None
                        if getattr(session, field) != new_val:
                            setattr(session, field, new_val)
                            session_changed = True
                    except ValueError:
                        continue
                else:
                    if getattr(session, field) != val:
                        setattr(session, field, val)
                        session_changed = True
        if session_changed:
            any_changes = True
    if any_changes:
        db.session.commit()
        sync_ledsess()
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return redirect(url_for('view_logs', _t=timestamp))










@app.route('/add_session', methods=['POST'])
@login_required
def add_session():
    form = request.form

    try:
        new_session = SessionRecord(  # type: ignore
            date=pd.to_datetime(form.get('date')).date() if form.get('date') else None,  # type: ignore
            location=form.get('location'),  # type: ignore
            type=form.get('type'),  # type: ignore
            stakes=form.get('stakes'),  # type: ignore
            time_in=parse_time(form.get('time_in')),  # type: ignore
            time_out=parse_time(form.get('time_out')),  # type: ignore
            money_in=float(form.get('money_in') or 0),  # type: ignore
            money_out=float(form.get('money_out') or 0),  # type: ignore
            comps_in=float(form.get('comps_in') or 0),  # type: ignore
            comps_out=float(form.get('comps_out') or 0),  # type: ignore
            tips=float(form.get('tips') or 0),  # type: ignore
            user_id=current_user.id  # type: ignore # ✅ correctly assign user ID
        )

        db.session.add(new_session)
        db.session.commit()
        sync_ledsess()

    except Exception as e:
        print("Error adding session:", e)

    return redirect(url_for('dashboard'))





@app.route('/banking')
@login_required
def view_banking():
    sessions = SessionRecord.query.filter_by(user_id=current_user.id).all()
    banks = BankRecord.query.filter_by(user_id=current_user.id).order_by(BankRecord.name).all()
    ledger = LedgerRecord.query.filter_by(user_id=current_user.id).order_by(LedgerRecord.date.desc()).all()

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
@login_required
def add_bank():
    name = request.form.get('bank_name')
    if name:
        new_bank = BankRecord(name=name.strip(), user_id=current_user.id)  # type: ignore
        db.session.add(new_bank)
        db.session.commit()
    return redirect(url_for('view_banking'))





@app.route('/delete_bank/<int:bank_id>', methods=['POST'])
@login_required
def delete_bank(bank_id):
    bank = BankRecord.query.get(bank_id)
    if bank and bank.user_id == current_user.id:
        db.session.delete(bank)
        db.session.commit()
    return redirect(url_for('view_banking'))





@app.route('/comps')
@login_required
def view_comps():
    from sqlalchemy import func

    # Get self comps and gift comps for the logged-in user
    self_comps = CompRecord.query.filter_by(user_id=current_user.id).all()
    gift_comps = GiftRecord.query.filter_by(user_id=current_user.id).all()

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



@app.route('/update-ledger', methods=['POST'])
@login_required
def update_ledger():
    form = request.form

    try:
        new_entry = LedgerRecord(  # type: ignore
            date=pd.to_datetime(form.get('date')).date(),  # type: ignore
            account=form.get('account'),  # type: ignore
            withdrawal=float(form.get('withdrawal') or 0),  # type: ignore
            deposit=float(form.get('deposit') or 0),  # type: ignore
            venture=form.get('venture'),  # type: ignore
            user_id=current_user.id  # type: ignore # ✅ secure association
        )
        db.session.add(new_entry)
        db.session.commit()
        sync_ledsess()

    except Exception as e:
        print("Error saving ledger entry:", e)

    return redirect(url_for('view_banking'))



@app.route('/ledger')
@login_required
def view_ledger():
    ledger_entries = LedgerRecord.query.filter_by(user_id=current_user.id).order_by(LedgerRecord.date.desc()).all()
    return render_template('ledger.html', ledger=ledger_entries)




@app.route('/edit-ledger/<int:ledger_id>', methods=['POST'])
@login_required
def edit_ledger_entry(ledger_id):
    entry = LedgerRecord.query.get(ledger_id)
    if entry and entry.user_id == current_user.id:
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
@login_required
def view_blackjack():
    sync_blackjack_sessions()
    from logs import BlackjackSession, SessionRecord, LedgerRecord
    # Get all blackjack sessions for this user
    sessions = (
        db.session.query(SessionRecord, BlackjackSession)
        .join(BlackjackSession, BlackjackSession.session_id == SessionRecord.id)
        .filter(SessionRecord.user_id == current_user.id, SessionRecord.type == 'Blackjack')
        .order_by(SessionRecord.date.desc(), SessionRecord.time_in.desc())
        .all()
    )
    # Prepare data for template
    records = []
    total_sessions = 0
    total_hours = 0.0
    total_profit = 0.0
    best_session = float('-inf')
    worst_session = float('inf')
    for s, bj in sessions:
        profit = (s.money_out or 0) - (s.money_in or 0)
        # Calculate duration in hours
        if s.time_in and s.time_out:
            duration_hours = (datetime.combine(s.date, s.time_out) - datetime.combine(s.date, s.time_in)).total_seconds() / 3600
            if duration_hours > 0:
                hourly_rate = profit / duration_hours
            else:
                hourly_rate = None
        else:
            duration_hours = None
            hourly_rate = None
        records.append({
            'id': bj.id,
            'date': s.date,
            'change': profit,
            'source': 'session',
            'spread': bj.spread or '',
            'game_speed': bj.game_speed or '',
            'game_rules': bj.game_rules or '',
            'system': bj.system or '',
            'duration_hours': duration_hours,
            'hourly_rate': hourly_rate
        })
        total_sessions += 1
        if s.time_in and s.time_out:
            duration = (datetime.combine(s.date, s.time_out) - datetime.combine(s.date, s.time_in)).total_seconds() / 3600
            total_hours += duration
        if profit > best_session:
            best_session = profit
        if profit < worst_session:
            worst_session = profit
        total_profit += profit
    if total_sessions == 0:
        best_session = 0.0
        worst_session = 0.0
    # Blackjack P/L chart (cumulative profit over time)
    # --- FIX: plot chart in chronological order ---
    sessions_chrono = list(reversed(sessions))
    chart_points = []
    cumulative = 0
    hours = 0
    for s, bj in sessions_chrono:
        profit = (s.money_out or 0) - (s.money_in or 0)
        cumulative += profit
        if s.time_in and s.time_out:
            duration = (datetime.combine(s.date, s.time_out) - datetime.combine(s.date, s.time_in)).total_seconds() / 3600
            hours += duration
        chart_points.append({'x': round(hours, 2), 'y': round(cumulative, 2)})
    # Ensure chart always starts at x=0
    if not chart_points or chart_points[0]['x'] != 0:
        chart_points = [{'x': 0, 'y': 0}] + chart_points
    # Blackjack Bankroll chart (from ledger and sessions)
    ledger_rows = LedgerRecord.query.filter_by(user_id=current_user.id, venture='Blackjack').order_by(LedgerRecord.date).all()
    combined = []
    for s, bj in sessions_chrono:
        combined.append({'date': s.date, 'change': (s.money_out or 0) - (s.money_in or 0)})
    for l in ledger_rows:
        combined.append({'date': l.date, 'change': (l.withdrawal or 0) - (l.deposit or 0)})
    combined.sort(key=lambda x: x['date'])
    bankroll_points = []
    bankroll = 0
    for item in combined:
        bankroll += item['change']
        bankroll_points.append({'x': item['date'].isoformat(), 'y': round(bankroll, 2)})
    bj_stats = {
        'total_sessions': total_sessions,
        'total_hours': total_hours,
        'total_profit': total_profit,
        'best_session': best_session,
        'worst_session': worst_session
    }
    return render_template('blackjack.html', records=records, bj_chart=chart_points, bj_bankroll=bankroll_points, bj_stats=bj_stats)









from logs import CompRecord  # ensure CompRecord is imported

@app.route('/log_comp', methods=['POST'])
@login_required
def log_comp():
    form = request.form

    try:
        log_comp = CompRecord(
            date=pd.to_datetime(form.get('date')).date() if form.get('date') else None,
            location=form.get('location'),
            type=form.get('type'),
            value=form.get('value'),
            item=form.get('item'),
            user_id=current_user.id  # ✅ associate with logged-in user
        )

        db.session.add(log_comp)
        db.session.commit()

    except Exception as e:
        print("Error logging comp:", e)

    return redirect(url_for('view_comps'))


from logs import GiftRecord  # ensure GiftRecord is imported




@app.route('/log_gift', methods=['POST'])
@login_required
def log_gift():
    form = request.form

    try:
        log_gift = GiftRecord(
            date=pd.to_datetime(form.get('date')).date() if form.get('date') else None,
            location=form.get('location'),
            type=form.get('type'),
            value=form.get('value'),
            item=form.get('item'),
            user_id=current_user.id  # ✅ secure user-specific association
        )

        db.session.add(log_gift)
        db.session.commit()

    except Exception as e:
        print("Error logging gift:", e)

    return redirect(url_for('view_comps'))






from logs import LocationRecord  # add this at the top if not already imported

@app.route('/add_location', methods=['POST'])
@login_required
def add_location():
    name = request.form.get('name')
    color = request.form.get('color')
    if name and color:
        new_location = LocationRecord(name=name.strip(), color=color, note="", user_id=current_user.id)
        db.session.add(new_location)
        db.session.commit()
    return redirect(url_for('view_locations'))

@app.route('/add_location_note/<int:location_id>', methods=['POST'])
@login_required
def add_location_note(location_id):
    location = LocationRecord.query.get(location_id)
    if location and location.user_id == current_user.id:
        content = request.form.get('content', '').strip()
        if content:
            new_note = LocationNote(
                location_id=location_id,
                user_id=current_user.id,
                content=content
            )
            db.session.add(new_note)
            db.session.commit()
    return redirect(url_for('view_locations'))

@app.route('/edit_location_note/<int:note_id>', methods=['POST'])
@login_required
def edit_location_note(note_id):
    note = LocationNote.query.get(note_id)
    if note and note.user_id == current_user.id:
        content = request.form.get('content', '').strip()
        if content:
            note.content = content
            note.updated_at = datetime.utcnow()
            db.session.commit()
    return redirect(url_for('view_locations'))

@app.route('/delete_location_note/<int:note_id>', methods=['POST'])
@login_required
def delete_location_note(note_id):
    note = LocationNote.query.get(note_id)
    if note and note.user_id == current_user.id:
        db.session.delete(note)
        db.session.commit()
    return redirect(url_for('view_locations'))

@app.route('/update_location_note/<int:location_id>', methods=['POST'])
@login_required
def update_location_note(location_id):
    location = LocationRecord.query.get(location_id)
    if location and location.user_id == current_user.id:
        location.note = request.form.get('note') or ""
        db.session.commit()
    return redirect(url_for('view_locations'))






@app.route('/api/update_location_color/<int:location_id>', methods=['POST'])
@login_required
def update_location_color(location_id):
    color = request.form.get('color')
    location = LocationRecord.query.get(location_id)
    if location and location.user_id == current_user.id and color:
        location.color = color
        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False), 400




@app.route('/delete_location/<int:location_id>', methods=['POST'])
@login_required
def delete_location(location_id):
    location = LocationRecord.query.get(location_id)
    if location and location.user_id == current_user.id:
        # Delete all notes for this location
        LocationNote.query.filter_by(location_id=location_id, user_id=current_user.id).delete()
        db.session.delete(location)
        db.session.commit()
    return redirect(url_for('view_locations'))





@app.route('/locations')
@login_required
def view_locations():
    # Auto-populate locations from SessionRecord if missing
    session_locations = set(s.location for s in SessionRecord.query.filter_by(user_id=current_user.id).all() if s.location)
    existing_locations = {loc.name for loc in LocationRecord.query.filter_by(user_id=current_user.id).all()}
    missing = session_locations - existing_locations
    for name in missing:
        color = random_color()
        new_loc = LocationRecord(name=name, color=color, note="", user_id=current_user.id)
        db.session.add(new_loc)
    if missing:
        db.session.commit()

    sessions = SessionRecord.query.filter_by(user_id=current_user.id).all()
    locations = LocationRecord.query.filter_by(user_id=current_user.id).all()

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

    # Get notes for each location
    location_notes = {}
    for loc in locations:
        notes = LocationNote.query.filter_by(location_id=loc.id, user_id=current_user.id).order_by(LocationNote.created_at.desc()).all()
        location_notes[loc.id] = notes

    return render_template('locations.html', locations=locations, summary=summary, location_notes=location_notes)





from flask_login import current_user

def sync_ledsess():
    from logs import db, LedSessRecord, LedgerRecord, SessionRecord

    ledger_count = LedgerRecord.query.filter_by(user_id=current_user.id).count()
    session_count = SessionRecord.query.filter_by(user_id=current_user.id).count()
    ledsess_count = LedSessRecord.query.filter_by(user_id=current_user.id).count()
    if ledger_count == 0 and session_count == 0:
        print('[sync_ledsess] No data to sync for user', current_user.id)
        return

    seen = {}
    print(f'[sync_ledsess] Rebuilding LedSess for user {current_user.id}')

    for entry in LedgerRecord.query.filter_by(user_id=current_user.id).all():
        if not entry.date or not entry.venture:
            continue
        delta = (entry.deposit or 0) - (entry.withdrawal or 0)
        if delta == 0:
            continue
        key = (entry.date, entry.account, round(-delta, 2))
        seen[key] = LedSessRecord(  # type: ignore
            date=entry.date,  # type: ignore
            type=entry.account,  # type: ignore
            value=-delta,  # type: ignore
            user_id=current_user.id  # type: ignore
        )
        print(f'  [Ledger] {entry.date} {entry.account} {round(-delta,2)}')

    for sess in SessionRecord.query.filter_by(user_id=current_user.id).all():
        if not sess.date or not sess.type:
            continue
        profit = (sess.money_out or 0) - (sess.money_in or 0)
        if profit == 0:
            continue
        key = (sess.date, sess.type, round(profit, 2))
        seen[key] = LedSessRecord(  # type: ignore
            date=sess.date,  # type: ignore
            type=sess.type,  # type: ignore
            value=profit,  # type: ignore
            user_id=current_user.id  # type: ignore
        )
        print(f'  [Session] {sess.date} {sess.type} {round(profit,2)}')

    LedSessRecord.query.filter_by(user_id=current_user.id).delete()
    if seen:
        db.session.bulk_save_objects(seen.values())
    db.session.commit()
    print(f'[sync_ledsess] {len(seen)} LedSessRecords created for user {current_user.id}')


def sync_blackjack_sessions():
    """Sync BlackjackSession records from SessionRecord where type is 'Blackjack'"""
    from logs import BlackjackSession, SessionRecord
    
    # Get all Blackjack sessions that don't have corresponding BlackjackSession records
    blackjack_sessions = (
        SessionRecord.query
        .filter_by(user_id=current_user.id, type='Blackjack')
        .all()
    )
    
    created_count = 0
    for session in blackjack_sessions:
        # Check if BlackjackSession already exists for this session
        existing = BlackjackSession.query.filter_by(session_id=session.id).first()
        if not existing:
            # Create new BlackjackSession record
            bj_session = BlackjackSession(  # type: ignore
                session_id=session.id,  # type: ignore
                user_id=current_user.id,  # type: ignore
                spread='',  # type: ignore
                game_speed='',  # type: ignore
                game_rules='',  # type: ignore
                system=''  # type: ignore
            )
            db.session.add(bj_session)
            created_count += 1
    
    if created_count > 0:
        db.session.commit()
        print(f'[sync_blackjack_sessions] Created {created_count} BlackjackSession records for user {current_user.id}')
    else:
        print(f'[sync_blackjack_sessions] No new BlackjackSession records needed for user {current_user.id}')




from logs import LedSessRecord

@app.route('/ledsess')
@login_required
def view_ledsess():
    entries = LedSessRecord.query.filter_by(user_id=current_user.id).order_by(LedSessRecord.date, LedSessRecord.id).all()
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
@login_required
def refresh_ledsess():
    sync_ledsess()
    return redirect(url_for('view_ledsess'))











@app.route('/api/recent_sessions')
@login_required
def api_recent_sessions():
    from logs import SessionRecord
    from datetime import datetime
    sessions = (
        SessionRecord.query
        .filter_by(user_id=current_user.id)
        .order_by(SessionRecord.date.desc(), SessionRecord.time_in.desc())
        .limit(10)
        .all()
    )
    result = []
    for s in sessions:
        money_in = s.money_in or 0
        money_out = s.money_out or 0
        profit = money_out - money_in
        if s.time_in and s.time_out:
            hours = (datetime.combine(s.date, s.time_out) - datetime.combine(s.date, s.time_in)).total_seconds() / 3600
        else:
            hours = 0
        result.append({
            'type': s.type or '',
            'amount': round(profit, 2),
            'hours': round(hours, 2),
            'date': s.date.strftime('%m/%d') if s.date else ''
        })
    return jsonify(result)

@app.route('/api/blackjack_spreads', methods=['GET', 'POST'])
@login_required
def api_blackjack_spreads():
    if request.method == 'POST':
        value = request.form.get('value', '').strip()
        if not value:
            return jsonify(success=False, error='No value provided'), 400
        # Prevent duplicates for this user
        if BlackjackSpread.query.filter_by(user_id=current_user.id, value=value).first():
            return jsonify(success=False, error='Spread already exists'), 400
        spread = BlackjackSpread(user_id=current_user.id, value=value)
        db.session.add(spread)
        db.session.commit()
        return jsonify(success=True, id=spread.id, value=spread.value)
    # GET: return all for this user
    spreads = BlackjackSpread.query.filter_by(user_id=current_user.id).all()
    return jsonify([{'id': s.id, 'value': s.value} for s in spreads])

@app.route('/api/blackjack_spreads/<int:spread_id>', methods=['DELETE'])
@login_required
def api_delete_blackjack_spread(spread_id):
    spread = BlackjackSpread.query.get(spread_id)
    if not spread or spread.user_id != current_user.id:
        return jsonify(success=False, error='Not found'), 404
    db.session.delete(spread)
    db.session.commit()
    return jsonify(success=True)

@app.route('/api/blackjack_gamerules', methods=['GET', 'POST'])
@login_required
def api_blackjack_gamerules():
    if request.method == 'POST':
        value = request.form.get('value', '').strip()
        if not value:
            return jsonify(success=False, error='No value provided'), 400
        if BlackjackGameRule.query.filter_by(user_id=current_user.id, value=value).first():
            return jsonify(success=False, error='Game rule already exists'), 400
        rule = BlackjackGameRule(user_id=current_user.id, value=value)
        db.session.add(rule)
        db.session.commit()
        return jsonify(success=True, id=rule.id, value=rule.value)
    rules = BlackjackGameRule.query.filter_by(user_id=current_user.id).all()
    return jsonify([{'id': r.id, 'value': r.value} for r in rules])

@app.route('/api/blackjack_gamerules/<int:rule_id>', methods=['DELETE'])
@login_required
def api_delete_blackjack_gamerule(rule_id):
    rule = BlackjackGameRule.query.get(rule_id)
    if not rule or rule.user_id != current_user.id:
        return jsonify(success=False, error='Not found'), 404
    db.session.delete(rule)
    db.session.commit()
    return jsonify(success=True)

@app.route('/api/blackjack_session/<int:bj_id>', methods=['POST'])
@login_required
def update_blackjack_session(bj_id):
    from logs import BlackjackSession
    bj = BlackjackSession.query.get(bj_id)
    if not bj or bj.user_id != current_user.id:
        return jsonify(success=False, error='Not found'), 404
    data = request.get_json() or request.form
    for field in ['spread', 'game_speed', 'game_rules', 'system']:
        if field in data:
            setattr(bj, field, data[field])
    db.session.commit()
    return jsonify(success=True)

@app.route('/landing-standalone')
def landing_standalone():
    return render_template('landing-standalone.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555, debug=False)

