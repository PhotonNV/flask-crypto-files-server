from flask import Flask, request
from dotenv import load_dotenv
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import os
import io
import re
import uuid
import jwt
import datetime
from functools import wraps
from cryptography.fernet import Fernet

app = Flask(__name__)

load_dotenv()

HOST = os.getenv('HOST')
PORT = os.getenv('PORT')
TOKEN_LIFE_MINUTES = int(os.getenv('TOKEN_LIFE_MINUTES'))
SECRET_KEY = os.getenv('SECRET_KEY')

app.config["MONGO_URI"] = 'mongodb://' + os.getenv('MONGO_HOST') +\
                          ':' + os.getenv('MONGO_PORT') + '/' + os.getenv('MONGO_DB')
mongo = PyMongo(app)


def chek_correct_file_id(file_id):
    return re.match(r'\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b', file_id)


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
            {'public_id': current_user['public_id'],
             'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=TOKEN_LIFE_MINUTES)}, SECRET_KEY)
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
    return 'Login is OK, your name: ' + current_user['name'] + '\n', 200


@app.route('/load', methods=['POST'])
@token_required
def load(current_user):
    open_date = request.get_data(cache=False, as_text=False, parse_form_data=False)
    cipher_key = Fernet.generate_key()
    cipher = Fernet(cipher_key)
    encrypted_data = cipher.encrypt(open_date)
    fs_encrypted_data = io.BytesIO(encrypted_data)
    file_id = str(uuid.uuid4())
    mongo.save_file(filename=file_id, fileobj=fs_encrypted_data, user_save=current_user['name'],
                    crypto_key=cipher_key.decode())
    return file_id, 200


@app.route('/get_crypto_key/<file_id>', methods=['GET'])
@token_required
def get_crypto_key(current_user, file_id):
    if not chek_correct_file_id(file_id):
        return 'The request does not contain correct file ID \n', 400

    get_file_info = mongo.db.fs.files.find_one({'user_save': current_user['name'], 'filename': file_id})
    if get_file_info is None:
        return 'No file with such a file ID was found \n', 404
    return get_file_info['crypto_key'], 200


@app.route('/download/<file_id>', methods=['GET'])
@token_required
def download(current_user, file_id):
    if not chek_correct_file_id(file_id):
        return 'The request does not contain correct file ID \n', 400

    if mongo.db.fs.files.find_one({'filename': file_id}) is None:
        return 'No file with such a file ID was found \n', 404
    return mongo.send_file(filename=file_id)


if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)
