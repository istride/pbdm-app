from flask import Flask, render_template, request, redirect, url_for, session
from dash_app.dashboard import init_dashboard
from scripts import translate_odk
from scripts.odk_to_pbdm import Insect
import os
from pyodk.client import Client

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Needed for session management

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(''))
CONFIG_DIR = os.path.join(BASE_DIR, "pbdm-flask-app", "pyodk_config.toml")
FILES_DIR = os.path.join(BASE_DIR, "pbdm-flask-app", "flask-app", "files")
# Authenticate with ODK Central
client = Client(config_path=CONFIG_DIR)
client.projects.default_project_id = 10
client.forms.default_form_id = "pbdm_bdf"
client.submissions.default_form_id = "pbdm_bdf"

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/odk', methods=['GET', 'POST'])
def odk():
    if request.method == 'POST':
        odk_form_id = request.form['submission']
        session['odk_form_id'] = odk_form_id
        return redirect(url_for('interact'))
    
    odk_list = translate_odk.get_org_names(client)
    return render_template('odk.html', submissions=odk_list)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['json_file']
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        session['uploaded_file'] = filepath
        return redirect(url_for('interact'))
    return render_template('upload.html')

@app.route('/interact', methods=['GET', 'POST'])
def interact():
    odk_form_id = session.get('odk_form_id')

    if not odk_form_id:
        odk_form_id = next(iter(translate_odk.get_org_names(client)))
        

    if request.method == 'POST':
        user_input = request.form.to_dict()
        session['user_input'] = user_input
        return redirect(url_for('dashboard'))
    
    data = translate_odk.create_pbdm_data(client, odk_form_id)
    pbdm_data = Insect(**data)
    pbdm_data.to_json(FILES_DIR, "pbdm_data.json")
    options = {
        'text': f'Enter your name {odk_form_id}',
        'yes_no': 'Do you confirm?'
    }
    return render_template('interact.html', options=options)

@app.route('/dashboard')
def dashboard():
    from dash_app.dashboard import create_dashboard
    return create_dashboard(request)

dash_app = init_dashboard(app)

if __name__ == '__main__':
    app.run(debug=True)