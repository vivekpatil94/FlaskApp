from . import app
import os
from flask import Flask, request, abort, jsonify, Blueprint
from functools import wraps
from .component import getRoleAR
import jwt 
import datetime

authentication = Blueprint('authentication',__name__)

def require_auth(permission=''):
    def require_auth_pro(f):
        @wraps(f)
        def wrapper(*args,**kwargs):
            #get the token 
            token = get_auth_token()
            #decode the token and get the payload
            payload = decode_auth_token(token)
            #check if the user has authorized to access
            check_permissions(permission, payload)
            #return the payload
            return f(payload,*args,**kwargs)
        return wrapper
    return require_auth_pro

def get_auth_token():
        # check from the token if authenticate and return it  
        if 'Authorization' not in request.headers:
            abort(401, description='الترخيص مفقود في الطلب')
        auth_header = request.headers['Authorization']
        auth_parts = auth_header.split(' ')
        if len(auth_parts) != 2:
            abort(401, description='ترخيص غير صالح')
        elif auth_parts[0].lower() != 'bearer':
            abort(401, description='ترخيص غير صالح')   
        #return token only 
        return auth_parts[1]

def decode_auth_token(auth_token):
    try:
        #if there any exception with token either expired or invalid will detected 
        payload = jwt.decode(auth_token, app.config.get('SECRET_KEY'),algorithms=['HS256'])
        #return the payload
        return payload
    except jwt.ExpiredSignatureError:
        abort(403, description='انتهت صلاحية الترخيص')
    except jwt.InvalidTokenError:
        abort(403, description='رمز غير صحيح')

def check_permissions(permission, payload):
    if 'permissions' not in payload:
        abort(400, description='الإذن مفقود في الطلب')
    if payload['permissions'] not in permission:
        abort(401, description='لا يوجد إذن للوصول للصفحة')
    return True
     
def initiate_token(uid,permission,fname,lname,hasSchool):

    roleAR = getRoleAR(permission)

    return jwt.encode({
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=5),
            'iat': datetime.datetime.utcnow(),
            'sub' : uid,
            'data': {
                'fname': fname,
                'lname': lname,
                'role': roleAR,
                'hasSchool': hasSchool
            },
            'permissions' : permission
        },
        app.config['SECRET_KEY'],
        algorithm='HS256')
        #token = initiate_token('1245','Educational_Supervisor','Ahmad','Mostafa')

def initiate_reset_password_token(uid,email):

    return jwt.encode({
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
            'iat': datetime.datetime.utcnow(),
            'sub' : uid,
            'data': {
                'email': email
            }
        },
        app.config['SECRET_KEY'],
        algorithm='HS256')




