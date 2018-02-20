from flask import Flask, request, Response
from logging.handlers import RotatingFileHandler
from expire import ExpirationThread
import json
import time
import logging
import threading
import random

app = Flask(__name__)

""" Constants """

# API RESOURCE
v = '/v1'
keys = v + '/keys'
reset= v + '/reset'
backup = v + '/backup'
stop_expire_thread = v + '/expire/stop'
resp_typ = 'application/json'

# KEYWORDS
port = 9001
KEY = 'key'
VAL = 'value'
CREATE_TIME = 'createTime'
LIFE_TIME = 'lifeTime'

# MESSAGES
FOUND_MSG = 'Found key value'
EXPIRED_KEY_MSG = 'Deleted expired key: %s'
NOT_FOUND_MSG = 'Not found key: %s'
ADD_MSG = "Added key: %s"
UPDATE_MSG = "Updated key: %s"
DUPLICATE_MSG = "Duplicate key: %s"
BAD_MSG = "Bad Request"
DELETE_MSG = "Deleted key: %s"

@app.route('/')
def index():
    return 'Hello World! Welcome to the TTL Cache'


def parse_req(req):
    """
    Parse the request for key, value and life time
    :param req:
    :return:
    """
    r = json.loads(req.get_data())
    app.logger.debug("Request: {}".format(r))
    data = {}
    data[KEY] = r[KEY]
    data[VAL] = r[VAL]
    data[CREATE_TIME] = time.time()
    if LIFE_TIME in r.keys():
        data[LIFE_TIME] = r[LIFE_TIME]
    return data


def check_if_expired(key):
    k = app.cache[key]
    c_time = time.time()
    exp_time = k[CREATE_TIME] + (k[LIFE_TIME]*60.0)
    flag = (c_time >= exp_time)
    app.logger.debug("Expiry check for key %s %s >= %s, %s" % (key, c_time, exp_time, flag))
    if LIFE_TIME in k.keys() and flag:
        app.cache.pop(key)
        app.keys_to_expire.remove(key)
        app.logger.info(EXPIRED_KEY_MSG % key)
        return True
    return False


def format_response(msg_str, status, data=None):
    msg = {}
    msg['Message'] = msg_str
    msg['StatusCode'] = status
    if data:
        msg['Data'] = data
    return Response(json.dumps(msg), status=status, mimetype=resp_typ)

@app.route(keys, methods=['POST'])
def add():
    """
    Add a new key value pair to the cache
    :return:
    """
    try:
        data = parse_req(request)
        if data[KEY] not in app.cache:
            app.cache[data[KEY]] = data
            if LIFE_TIME in data.keys():
                app.keys_to_expire.append(data[KEY])
        else:
            return format_response(DUPLICATE_MSG % data[KEY], 400)
    except Exception:
        return format_response(BAD_MSG, 400)
    return format_response(ADD_MSG % data[KEY], 200)


@app.route(keys + '/<key>', methods=['PUT'])
def update(key):
    """
    Update the key value pair from the cache
    :param key:
    :return:
    """
    try:
        if key in app.cache.keys():
            data = parse_req(request)
            app.cache[data[KEY]] = data
            if LIFE_TIME in data.keys():
                app.keys_to_expire.add(data[KEY])
        else:
            return format_response(NOT_FOUND_MSG % key, status=400)
    except Exception:
        return format_response(BAD_MSG, 400)
    return format_response(UPDATE_MSG%key, status=200)


@app.route(keys + '/<key>', methods=['GET'])
def get(key):
    """
    Get key value pair from the cache
    :param key:
    :return:
    """
    try:
        if check_if_expired(key):
            raise Exception
        data = app.cache[key]
    except Exception:
        return format_response(NOT_FOUND_MSG % key, status=404)
    return format_response(FOUND_MSG, status=200, data=data)


@app.route(keys, methods=['GET'])
def list_all():
    """
    List the cache
    :return:
    """
    try:
        data = app.cache
    except Exception:
        return format_response(NOT_FOUND_MSG, status=404)
    return format_response(FOUND_MSG, status=200, data=data)


@app.route(keys + '/<key>', methods=['DELETE'])
def delete(key):
    """
    Delete a key value pair from the cache
    :param key:
    :return:
    """
    try:
        app.cache.pop(key)
        if key in app.keys_to_expire:
            app.keys_to_expire.remove(key)
    except Exception:
        return format_response(NOT_FOUND_MSG % key, status=404)
    return format_response(DELETE_MSG % key, status=200)


@app.route(reset, methods=['PUT'])
def reset():
    """
    Reset the cache
    :return:
    """
    try:
        app.cache = {}
        app.keys_to_expire = set()
    except Exception:
        return format_response(BAD_MSG, status=404)
    return format_response("Reset all", status=200)


@app.route(backup, methods=['PUT'])
def backup():
    """
    Backup the cache
    :return:
    """
    return format_response("Not implemented", status=200)

@app.route(stop_expire_thread, methods=['PUT'])
def stop_expiration():
    """
    Backup the cache
    :return:
    """
    try:
        app.expire_thread.stop()
    except:
        return format_response(BAD_MSG, status=404)
    return format_response("Stopped Expiration thread", status=200)

def setup_logging():
    """
    Set logging handler
    """
    handler = RotatingFileHandler('ttl_cache.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)


def setup_cache_ds():
    """
    Initialize cache data structures
    """
    app.cache = {}
    app.keys_to_expire = []


def expiration_workflow(percent_workload):
    """
    For given percent of keys in keys_to_expire dict:
      Pick one random key
      Check if it is expired
        Delete

    :param percent_workload:
    """
    n = len(app.keys_to_expire)
    app.logger.debug("Current count keys in expiration queue: %s" % n)
    range = int(n*percent_workload/100)
    print range, percent_workload
    for i in xrange(range):
        key = random.randint(0, n-1)
        app.logger.debug("Key to check for expiration: %s" % app.keys_to_expire[key])
        check_if_expired(app.keys_to_expire[key])


def start_expire_thread(frequency=1, percent_workload=25):
    app.expire_thread = ExpirationThread(frequency=frequency)
    t = threading.Thread(target=app.expire_thread.run, args=(expiration_workflow, percent_workload))
    t.start()

if __name__ == '__main__':
    try:
        # 1. Setup logging handler
        setup_logging()
        # 2. Initialize Cache
        setup_cache_ds()
        # 3. Start App
        app.logger.info("Starting Server --> localhost:%s" % port)
        # 4. Start expiration thread
        start_expire_thread()
        app.run(port=port, debug=True)
    except Exception:
        print("%s"%Exception.message)
