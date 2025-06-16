from flask import Flask, render_template, request
import pandas as pd
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/')
app.secret_key = 'SOME KEY'

some_text = "Hello, World!"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    elif request.method == 'POST':
        return ""
        username = request.form.get('username')
        password = request.form.get('password')

        if username == 'wheredablow' and password == 'legoland72':
            return 'Successful Login'
        else:
            return 'Login Failed'



@app.route('/file_upload', methods=['POST'])
def file_upload():
    file = request.files['file']

    if file.content_type == 'text/plain':
        return file.read().decode()
    elif file.content_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' or file.content_type == 'application/vnd.ms-excel' or file.content_type == 'text/plain':
        df = pd.read_excel(file)
        df = df.iloc[:, 1:]
        return df.to_html()



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555, debug=True)


