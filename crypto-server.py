from flask import Flask, request
from dotenv import load_dotenv
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
import jwt
import datetime
from functools import wraps

app = Flask(__name__)

load_dotenv()

HOST = os.getenv('HOST')
PORT = os.getenv('PORT')
SECRET_KEY = os.getenv('SECRET_KEY')
app.config["MONGO_URI"] = 'mongodb://' + os.getenv('MONGO_HOST') +\
                          ':' + os.getenv('MONGO_PORT') + '/' + os.getenv('MONGO_DB')
mongo = PyMongo(app)


@app.route('/registration', methods=['POST'])
def registration():
    min_char_in_login_user = 5
    new_user_name = request.headers.get('New_User_Name')
    new_user_password = request.headers.get('New_User_Password')
    if len(new_user_name) < min_char_in_login_user or len(new_user_password) < min_char_in_login_user:
        return 'The length of the login and password must be more than ' + str(min_char_in_login_user)\
               + ' characters \n', 400
    if mongo.db.users.find_one({'name': new_user_name}) is not None:
        return 'User ' + new_user_name + ' exist!', 400
    hash_password = generate_password_hash(new_user_password, method='sha256')
    mongo.db.users.insert_one({'public_id': str(uuid.uuid4()), 'name': new_user_name, 'password': hash_password})
    return 'Registration user ' + new_user_name + ' is done!', 200


@app.route('/login', methods=['GET'])
def login_user():
    user_name = request.headers.get('User_Name')
    user_password = request.headers.get('User_Password')
    if user_name is None or user_password is None:
        return 'Not login or password', 401

    current_user = mongo.db.users.find_one({'name': user_name})
    if current_user is not None and check_password_hash(current_user['password'], user_password):
        token = jwt.encode(
            {'public_id': current_user['public_id'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)},
            SECRET_KEY)
        return token.decode('UTF-8'), 200

    return 'Could not verify', 401


def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):

        token = None
        if 'x-access-tokens' in request.headers:
            token = request.headers['x-access-tokens']

        if not token:
            return 'A valid token is missing', 400

        try:
            data = jwt.decode(token, SECRET_KEY)
            current_user = mongo.db.users.find_one({'public_id': data['public_id']})

        except:
            return 'Token is invalid', 401

        return f(current_user, *args, **kwargs)
    return decorator


@app.route('/test_login', methods=['GET'])
@token_required
def test_login(current_user):
    return 'Login is OK, your name: '+ current_user['name'] + '\n', 200


if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)
