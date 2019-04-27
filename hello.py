from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_migrate import Migrate
from cloudant import Cloudant
from cloudant.result import Result, ResultByKey
import atexit
import os
import json
import uuid

app = Flask(__name__, static_url_path='')

db_name = 'pin_database'
client = None
db = None

if 'VCAP_SERVICES' in os.environ:
    vcap = json.loads(os.getenv('VCAP_SERVICES'))
    print('Found VCAP_SERVICES')
    if 'cloudantNoSQLDB' in vcap:
        creds = vcap['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)
elif "CLOUDANT_URL" in os.environ:
    client = Cloudant(os.environ['CLOUDANT_USERNAME'], os.environ['CLOUDANT_PASSWORD'], url=os.environ['CLOUDANT_URL'], connect=True)
    db = client.create_database(db_name, throw_on_exists=False)
elif os.path.isfile('vcap-local.json'):
    with open('vcap-local.json') as f:
        vcap = json.load(f)
        print('Found local VCAP_SERVICES')
        creds = vcap['services']['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)

# On IBM Cloud Cloud Foundry, get the port number from the environment variable PORT
# When running this app on the local machine, default the port to 8000
port = int(os.getenv('PORT', 8000))

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html', api_url='/api/pin')


@app.route('/api/pin', methods=['GET', 'POST', 'DELETE'])
def pin_API():
    pin_info = request.get_json()
    if request.method == 'POST':
        pin_id = pin_info.get('id')
        pin_latitude = pin_info.get('latitude')
        pin_longtitude = pin_info.get('longtitude')
        data = {
            '_id':  pin_id,
            'latitude': pin_latitude,
            'longtitude': pin_longtitude,
        }
        pin_document = db.create_document(data)
        return jsonify(pin_info)
    elif request.method == 'DELETE':
        pin_info = request.get_json()
        pin_id = pin_info.get('id')
        document = db[pin_id]
        document.delete()
        return jsonify(pin_info)
    else: # 'GET' method
        results = []
        pins_collection = Result(db.all_docs, include_docs=True)
        for pin in pins_collection:
            pin_document = pin['doc']
            pin_info = {
                'id': pin_document.get('_id'),
                'latitude': pin_document.get('latitude'),
                'longitude': pin_document.get('longtitude')
            }
            results.append(pin_info)
        return jsonify(results)


@app.route('/chat')
def chat():
    return render_template('chat.html')


@app.route('/contacts')
def contacts():
    return render_template('contacts.html')


@app.route('/alerts')
def alerts():
    return render_template('alerts.html')

@atexit.register
def shutdown():
    if client:
        client.disconnect()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)
