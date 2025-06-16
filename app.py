from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)
session_data = []  # in-memory list to store sessions

# HTML template with Jinja2 templating
template = """
<!doctype html>
<title>Stokalytics</title>
<h1>Dashboard</h1>

<form method="POST" action="{{ url_for('add_session') }}">
  <button type="submit" name="show_form" value="true">New Session</button>
</form>

{% if show_form %}
  <form method="POST" action="{{ url_for('submit_session') }}">
    <p><label>Date: <input type="date" name="date"></label></p>
    <p><label>Location: <input type="text" name="location"></label></p>
    <p><label>Type: <input type="text" name="type"></label></p>
    <p><label>Time In: <input type="time" name="time_in"></label></p>
    <p><label>Time Out: <input type="time" name="time_out"></label></p>
    <p><label>Money In: <input type="number" name="money_in"></label></p>
    <p><label>Money Out: <input type="number" name="money_out"></label></p>
    <p><label>Comps In: <input type="number" name="comps_in"></label></p>
    <p><label>Comps Out: <input type="number" name="comps_out"></label></p>
    <p><label>Tips: <input type="number" name="tips"></label></p>
    <p>
      <button type="submit">Submit Session</button>
      <a href="{{ url_for('add_session') }}"><button type="button">Back to Dashboard</button></a>
    </p>
  </form>
{% endif %}

{% if sessions %}
  <h2>Session Log</h2>
  <table border="1" cellpadding="5">
    <tr>
      <th>Date</th><th>Location</th><th>Type</th><th>Time In</th><th>Time Out</th>
      <th>Money In</th><th>Money Out</th><th>Comps In</th><th>Comps Out</th><th>Tips</th>
    </tr>
    {% for s in sessions %}
    <tr>
      <td>{{ s['date'] }}</td><td>{{ s['location'] }}</td><td>{{ s['type'] }}</td>
      <td>{{ s['time_in'] }}</td><td>{{ s['time_out'] }}</td>
      <td>{{ s['money_in'] }}</td><td>{{ s['money_out'] }}</td>
      <td>{{ s['comps_in'] }}</td><td>{{ s['comps_out'] }}</td><td>{{ s['tips'] }}</td>
    </tr>
    {% endfor %}
  </table>
{% endif %}
"""

@app.route('/', methods=['GET', 'POST'])
def add_session():
    show_form = request.method == 'POST' and request.form.get("show_form") == "true"
    return render_template_string(template, sessions=session_data, show_form=show_form)

@app.route('/submit', methods=['POST'])
def submit_session():
    data = {
        'date': request.form['date'],
        'location': request.form['location'],
        'type': request.form['type'],
        'time_in': request.form['time_in'],
        'time_out': request.form['time_out'],
        'money_in': request.form['money_in'],
        'money_out': request.form['money_out'],
        'comps_in': request.form['comps_in'],
        'comps_out': request.form['comps_out'],
        'tips': request.form['tips']
    }
    session_data.append(data)
    return redirect(url_for('add_session'))

if __name__ == '__main__':
    app.run(debug=True)
