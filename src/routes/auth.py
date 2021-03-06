import re
from flask import request, session
from werkzeug.security import generate_password_hash, check_password_hash
from ..app import app
from ..db import db
from ..models import User


@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'login' in session:
            try:
                return User.query.filter_by(uuid=session['login']).one().get_fields(), 200
            except db.NoResultFound:
                del session['login']
        return {}, 401

    else:
        if 'email' in request.form and 'password' in request.form:
            data = request.form
        elif isinstance(request.json, dict) and 'email' in request.json and 'password' in request.json:
            data = request.json
        else:
            return {}, 400

        try:
            user = User.query.filter_by(email=data['email'].lower().strip()).one()
            if check_password_hash(user.password, data['password']):
                session['login'] = user.uuid
                return user.get_fields(), 200
        except db.NoResultFound:
            session.pop('login', None)

        return {}, 401


@app.route('/auth/logout', methods=['GET', 'POST'])
def logout():
    session.pop('login', None)
    return {}, 200


@app.route('/auth/register', methods=['POST'])
def register():
    if 'email' in request.form and 'password' in request.form:
        data = request.form
    elif isinstance(request.json, dict) and 'email' in request.json and 'password' in request.json:
        data = request.json
    else:
        return {}, 400

    data['email'] = data['email'].lower().strip()
    if not re.match(r'^[\w\-\.]+@[\w\-\.]+(\.[\w\-\.]+){1,}$', data['email']) or \
       len(data['password']) < 4:
        return {}, 400

    if User.query.filter_by(email=data['email']).count() > 0:
        return {}, 409

    user = db.add(User(
        email=data['email'],
        password=generate_password_hash(data['password']),
        first_name=data.get('first_name', '').strip(),
        last_name=data.get('last_name', '').strip()
    ))

    db.session.commit()

    session['login'] = user.uuid
    return user.get_fields(), 200
