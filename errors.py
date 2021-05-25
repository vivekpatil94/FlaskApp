from . import app
from flask import jsonify, Blueprint

errors = Blueprint('errors',__name__)

#ERROR HANDLING 
@app.errorhandler(400)
def not_found400(error):
    return jsonify({
    'success': False, 
    'error': 400,
    'message': format(error) 
    }), 400

@app.errorhandler(401)
def not_found401(error):
    return jsonify({
    'success': False, 
    'error': 401,
    'message': format(error) 
    }), 401

@app.errorhandler(403)
def not_found402(error):
    return jsonify({
    'success': False, 
    'error': 403,
    'message': format(error) 
    }), 403

@app.errorhandler(404)
def not_found402(error):
    return jsonify({
    'success': False, 
    'error': 404,
    'message': format(error) 
    }), 404

@app.errorhandler(405)
def not_found402(error):
    return jsonify({
    'success': False, 
    'error': 405,
    'message': '405 Method Not Allowed error :'+ 'الطلب غير مسموح'
    }), 405

@app.errorhandler(500)
def not_found402(error):
    return jsonify({
    'success': False, 
    'error': 500,
    'message': '500 Internal Server error :'+'لا يمكن الوسول الى النظام في الوقت الحالي'
    }), 500
