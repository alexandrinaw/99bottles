import json
import os

import redis
import requests
from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   session, url_for)
from flask.ext.socketio import SocketIO, emit
from flask_oauthlib.client import OAuth

from constants import (APP_SECRET, CONSUMER_ID, CONSUMER_SECRET, HS_ID,
                       HS_SECRET, TARGET_ACCESS_TOKEN, TARGET_ID)

app = Flask(__name__)
# comment out when you're done testing
app.debug = True
app.secret_key = APP_SECRET #a secret string that will sign your session cookies
redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
redis = redis.from_url(redis_url)
socketio = SocketIO(app)

@app.route('/')
@app.route('/index.html')
def index():
    decrement_bottles()
    data = _get_data()
    return render_template('index.html', data=data)

@app.route('/webhook', methods=["GET"])
def webhook_verify():
    challenge = request.args.get('venmo_challenge')
    return challenge

@app.route('/webhook', methods=["POST"])
def broadcast_payment():
    data = request.data
    dataDict = json.loads(data)
    socketio.emit('payment', dataDict, True)
    return 'hey'

@socketio.on('my event')
def my_event(message):
    emit('my response', {'data': 'I\'m connected!'})

def decrement_bottles():
    bottles_of_beer = int(get_bottles()) - 1
    redis.set('bottles', bottles_of_beer)
    return bottles_of_beer

def get_bottles():
    bottles_of_beer = redis.get('bottles')
    if not bottles_of_beer:
        bottles_of_beer = 99
        redis.set('bottles', 99)
    elif bottles_of_beer == '0':
        bottles_of_beer = 99
        redis.set('bottles', 99)
    return bottles_of_beer

def _get_data():
    if session.get('venmo_token'):
        data = {'name': session['venmo_username'],
                'consumer_id': CONSUMER_ID,
                'access_token': session['venmo_token'],
                'signed_in': True
                }
    else:
        data = {'signed_in': False,
                'consumer_id': CONSUMER_ID
                }

    # hacker school login
    if (session.get('login')):
        data['hs_login'] = get_login()
        data['payments'] = get_payments()

    if (session.get('skip_venmo_login')):
        data['skip_venmo_login'] = True

    if (session.get('skip_hs_login')):
        data['skip_hs_login'] = True

    data['bottles'] = get_bottles()

    return data

@app.route('/feed', methods=["GET"])
def feed():
    decrement_bottles()
    data = _get_data()
    return render_template('feed2.html', data=data)

@app.route('/skip_hs_login', methods=["GET"])
def skip_hs_login():
    session['skip_hs_login'] = True
    return redirect(url_for('index'))

@app.route('/skip_venmo_login', methods=["GET"])
def skip_venmo_login():
    session['skip_venmo_login'] = True
    return redirect(url_for('index'))

@app.route('/make_charge', methods=["POST"])
def make_charge():
    access_token = request.form['access_token']
    note = request.form['note']
    amount = request.form['amount']

    payload = {
        "access_token":access_token,
        "note":note,
        "amount":amount,
        "user_id": TARGET_ID
    }

    url = "https://api.venmo.com/v1/payments"
    response = requests.post(url, payload)
    data = response.json()
    #pid = data['data']['payment']['id']
    #I really want to be able to automatically complete charges but can't figure out if that exists in the Venmo API yet :(
    #complete_charge(pid)
    return jsonify(data)

def complete_charge(pid):
    url = "https://api.venmo.com/v1/payments"
    payload = {
        "action": "approve",
        "resource_id": pid,
        "access_token": TARGET_ACCESS_TOKEN
    }
    requests.put(url, payload)

@app.route('/make_payment', methods=["POST"])
def make_payment():
    access_token = request.form['access_token']
    note = request.form['note']
    amount = request.form['amount']

    payload = {
        "access_token":access_token,
        "note":note,
        "amount":amount,
        "user_id": TARGET_ID
    }

    url = "https://api.venmo.com/v1/payments"
    response = requests.post(url, payload)
    data = response.json()
    try:
        if data['data']['payment']['status'] == 'settled':
            'Cheers!'
            return jsonify(data)
        else:
            return jsonify(data)
    except KeyError:
        return jsonify(data)

def get_payments():
    access_token = TARGET_ACCESS_TOKEN
    url = "https://api.venmo.com/v1/payments?access_token=" + access_token
    response = requests.get(url)
    data = response.json()
    return data['data']

@app.route('/get_balance')
def get_balance():
    url = "https://api.venmo.com/v1/me?access_token=%s" % TARGET_ACCESS_TOKEN
    response = requests.get(url)
    data = response.json()
    balance = data['data']['balance']
    return balance

@app.route('/oauth-authorized')
def oauth_authorized():
    AUTHORIZATION_CODE = request.args.get('code')
    data = {
        "client_id":CONSUMER_ID,
        "client_secret":CONSUMER_SECRET,
        "code":AUTHORIZATION_CODE
        }
    url = "https://api.venmo.com/v1/oauth/access_token"
    response = requests.post(url, data)
    response_dict = response.json()
    access_token = response_dict.get('access_token')
    user = response_dict.get('user')

    session['venmo_token'] = access_token
    session['venmo_username'] = user['username']

    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/logout_hs')
def logout_hs():
    session['login'] = None
    session['skip_hs_login'] = False
    return redirect(url_for('index'))

@app.route('/logout_venmo')
def logout_venmo():
    session['venmo_token'] = None
    session['venmo_username'] = None
    session['skip_venmo_login'] = False
    return redirect(url_for('index'))

auth = OAuth(app).remote_app(
    'recurse'
    , base_url         = 'https://www.recurse.com/api/v1/'
    , access_token_url = 'https://www.recurse.com/oauth/token'
    , authorize_url    = 'https://www.recurse.com/oauth/authorize'
    , consumer_key     = HS_ID
    , consumer_secret  = HS_SECRET
    , access_token_method='POST'
    )

def get_login():
    # our internal function to retrieve login data
    # knowledge of session['login'] is only in here, oauth_authorized, and logout
    return session.get('login')

@auth.tokengetter
def get_token(token=None):
    # a decorated tokengetter function is required by the oauth module
    return get_login()['oauth_token']

@app.route('/hs_login')
def login():
    if get_login():
        flash('You are already logged in.')
        return redirect(request.referrer or url_for('index'))
    else:
        afterward = request.args.get('next') or request.referrer or None
        landing = url_for('hs_authorized', next=afterward, _external=True)
        return auth.authorize(callback=landing)

@app.route('/hs-authorized')
@auth.authorized_handler
def hs_authorized(resp):
    try:
        # make a partial login session here, get the username later if this part works
        # keys into resp are probably different for different oauth providers, unfortunately
        session['login'] = dict(oauth_token=(resp['access_token'], resp['refresh_token']))
    except TypeError as exc:
        flash('The login request was gracefully declined. (TypeError: %s)' % exc)
        return redirect(url_for('index'))
    except KeyError as exc:
        flash('There was a problem with the response dictionary. (KeyError: %s) %s' % (exc, resp))
        return redirect(url_for('index'))
    # now get their username
    me = auth.get('people/me')
    if me.status == 200:
        session['login']['user'] = '{first_name} {last_name}'.format(**me.data)
        session['login']['email'] = me.data['email']
        session['login']['image'] = me.data['image']
    else:
        session['login']['user'] = 'Hacker Schooler'
    flash('You are logged in.')
    return redirect(request.args.get('next') or url_for('index'))

if __name__ == '__main__':
    socketio.run(app)
