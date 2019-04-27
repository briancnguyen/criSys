from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_migrate import Migrate

from cloudant import Cloudant
import atexit
import os
import json



app = Flask(__name__, static_url_path='')

db_name = 'mydb'
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
    if request.method == 'POST':
        pin_info = request.get_json()
        # pin_latitude = pin_info.get('latitude')
        # pin_longtitude = pin_info.get('longtitude')
        # new_pin = Pin(latitude=pin_latitude, longitude=pin_longtitude)
        # DB.session.add(new_pin)
        # DB.session.commit()
        return jsonify(pin_info)
    elif request.method == 'DELETE':
        pin_info = request.get_json()
        # deleted_pin = Pin.query.filter_by(id=pin_info.get('id')).first()
        # DB.session.delete(deleted_pin)
        # DB.session.commit()
        return jsonify(pin_info)
    else: # 'GET' method
        # pins = Pin.query.all()
        results = []
        # for pin in pins:
        #     pin_info = {
        #         'id': pin.id,
        #         'latitude': pin.latitude,
        #         'longitude': pin.longitude,
        #     }
        #     results.append(pin_info)
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


# /* Endpoint to greet and add a new visitor to database.
# * Send a POST request to localhost:8000/api/visitors with body
# * {
# *     "name": "Bob"
# * }
# */
@app.route('/api/visitors', methods=['GET'])
def get_visitor():
    if client:
        return jsonify(list(map(lambda doc: doc['name'], db)))
    else:
        print('No database')
        return jsonify([])

# /**
#  * Endpoint to get a JSON array of all the visitors in the database
#  * REST API example:
#  * <code>
#  * GET http://localhost:8000/api/visitors
#  * </code>
#  *
#  * Response:
#  * [ "Bob", "Jane" ]
#  * @return An array of all the visitor names
#  */
@app.route('/api/visitors', methods=['POST'])
def put_visitor():
    user = request.json['name']
    data = {'name':user}
    if client:
        my_document = db.create_document(data)
        data['_id'] = my_document['_id']
        return jsonify(data)
    else:
        print('No database')
        return jsonify(data)

@atexit.register
def shutdown():
    if client:
        client.disconnect()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)
