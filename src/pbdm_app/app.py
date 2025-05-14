from flask import Flask, render_template, request, redirect, url_for, session, Response
from pbdm_app.dash_app.dashboard import create_dashboard
from pbdm_app.scripts import translate_odk
from pbdm_app.scripts.odk_to_pbdm import Insect
import os
from pyodk.client import Client
from pbdm.functional_population.functional_population import FunctionalPopulation
# from pbdm_app.scripts.pbdm_to_psymple import pbdmRunner
import time
from werkzeug.middleware.dispatcher import DispatcherMiddleware

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Needed for session management

model_store = {}

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(''))
CONFIG_DIR = os.path.join(BASE_DIR, "pbdm-flask-app", "pyodk_config.toml")
FILES_DIR = os.path.join(BASE_DIR, "pbdm-flask-app", "flask-app", "files")
# Authenticate with ODK Central
# client = Client(config_path=CONFIG_DIR)
# client.projects.default_project_id = 10
# client.forms.default_form_id = "pbdm_bdf"
# client.submissions.default_form_id = "pbdm_bdf"
client = None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/odk', methods=['GET', 'POST'])
def odk():
    if request.method == 'POST':
        odk_form_id = request.form['submission']
        session['odk_form_id'] = odk_form_id
        return redirect(url_for('loading'))
    
    odk_list = translate_odk.get_org_names(client)
    return render_template('odk.html', submissions=odk_list)

@app.route('/start_processing')
def start_processing():
    odk_form_id = session.get('odk_form_id')
    return Response(compile_model(client, odk_form_id), content_type='text/event-stream')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['json_file']
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        session['uploaded_file'] = filepath
        return redirect(url_for('interact'))
    return render_template('upload.html')

@app.route('/loading')
def loading():
    return render_template('loading.html')

def compile_model(client, odk_form_id):
    
    data = translate_odk.create_pbdm_data(client, odk_form_id)
    yield 'data: script1_done\n\n'
    time.sleep(1)
    pbdm_object = Insect(**data)
    pbdm_data = pbdm_object.data
    #func_pop = FunctionalPopulation(**pbdm_data)

    pbdm_object.to_json(FILES_DIR, "pbdm_data.json")
    yield 'data: script2_done\n\n'
    time.sleep(1)

    
    # obj = pbdmRunner(pbdm_data)
    yield 'data: script3_done\n\n'  
    time.sleep(1)

    # model_store[odk_form_id] = obj
    yield 'data: done\n\n'
    
    


@app.route('/interact', methods=['GET', 'POST'])
def interact():
    odk_form_id = session.get('odk_form_id')

    if not odk_form_id:
        odk_form_id = next(iter(translate_odk.get_org_names(client)))

    obj = model_store.get(odk_form_id)
    initials = obj.generate_initial_conditions()

    options = []
    for var, value in initials.items():
        options.append({
        'name': var, 'type': "number", 'label': f'Initial condition for {var}', 'default': value
    })

    if request.method == 'POST':
        user_input = {param['name']: request.form.get(param['name']) for param in options}
        session['user_input'] = user_input
        return redirect(url_for('dashboard'))

    
    return render_template('interact.html', options=options)

"""
with app.app_context():
    dash_app = DispatcherMiddleware(app, {
        "/dashy": create_dashboard("/dashy/"),
    })
"""

dash_app = create_dashboard(app)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    from werkzeug.serving import run_simple
    app.run(debug=True)
    application = DispatcherMiddleware(app, {
        '/dash': dash_app
    })
    run_simple("localhost", 8050, application, use_reloader=True, use_debugger=True)
