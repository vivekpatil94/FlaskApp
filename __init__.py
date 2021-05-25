from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

# application setup 
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.environ.get('SQLALCHEMY_TRACK_MODIFICATIONS')
app.config['ACCOUNT'] = os.environ.get('ACCOUNT')
app.config['ACCOUNT_PASSWORD'] = os.environ.get('ACCOUNT_PASSWORD')

print(app.config.get('SQLALCHEMY_DATABASE_URI'))

db = SQLAlchemy(app)
cors = CORS(app)

migrate = Migrate(app, db,compare_type=True)


from .authentication import authentication
app.register_blueprint(authentication)

from .public_route import public_route
app.register_blueprint(public_route)

from .system_administrator.resources_route import resources_route
app.register_blueprint(resources_route)

from .school_manager.school_resource import school_resource
app.register_blueprint(school_resource)

from .laboratory_manager.lab_manager_route import lab_manager_route
app.register_blueprint(lab_manager_route)

from .practical_experiment.request_view import request_view
app.register_blueprint(request_view)

from .evaluate.evaluate_view import evaluate_view
app.register_blueprint(evaluate_view)

from .educational_supervisor.educational_supervisor_view import educational_supervisor_view
app.register_blueprint(educational_supervisor_view)

from .support.support_view import support_route
app.register_blueprint(support_route)

from .errors import errors
app.register_blueprint(errors)

from .component import initiate_evaluate_type
initiate_evaluate_type(db)

@app.route('/')
def index():
    return 'hello'

@app.route('/check', methods=['POST'])
def check():
    name = request.form.get('name')
    return name
