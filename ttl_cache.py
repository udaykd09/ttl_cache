from flask import Flask, request, Response
import json
import time

app = Flask(__name__)

""" Constants """
v = '/v1'
keys = v + '/keys'
reset= v + '/reset'
backup = v + '/backup'
resp_typ = 'application/json'
port = 9001
KEY = 'key'
VAL = 'value'
CREATE_TIME = 'createTime'
LIFE_TIME = 'lifeTime'

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
    print("Request: {}".format(r))
    data = {}
    data[KEY] = r[KEY]
    data[VAL] = r[VAL]
    data[CREATE_TIME] = time.time()
    if LIFE_TIME in r.keys():
        data[LIFE_TIME] = r[LIFE_TIME]
    return data


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
                app.keys_to_expire.add(data[KEY])
        else:
            return Response("Key already present", status=400, mimetype=resp_typ)
    except Exception:
        return Response("Bad Request", status=400, mimetype=resp_typ)
    return Response("Added Key {}".format(data['key']), status=200, mimetype=resp_typ)


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
            return Response("Key not found", status=400, mimetype=resp_typ)
    except Exception:
        return Response("Bad Request", status=400, mimetype=resp_typ)
    return Response("Added Key {}".format(data['key']), status=200, mimetype=resp_typ)


@app.route(keys + '/<key>', methods=['GET'])
def get(key):
    """
    Get key value pair from the cache
    :param key:
    :return:
    """
    try:
        data = app.cache[key]
    except Exception:
        return Response("Not Found", status=404, mimetype=resp_typ)

    return Response(json.dumps(data), status=200, mimetype=resp_typ)


@app.route(keys, methods=['GET'])
def list_all():
    """
    List the cache
    :return:
    """
    try:
        data = app.cache
    except Exception:
        return Response("Not Found", status=404, mimetype=resp_typ)

    return Response(json.dumps(data), status=200, mimetype=resp_typ)


@app.route(keys + '/<key>', methods=['DELETE'])
def delete(key):
    """
    Delete a key value pair from the cache
    :param key:
    :return:
    """
    try:
        app.cache.pop(key)
    except Exception:
        return Response("Not Found", status=404, mimetype=resp_typ)

    return Response("Deleted Key : {}".format(key), status=200, mimetype=resp_typ)


@app.route(reset, methods=['PUT'])
def reset():
    """
    Reset the cache
    :return:
    """
    app.cache = {}
    app.keys_to_expire = set()


@app.route(backup, methods=['PUT'])
def backup():
    """
    Backup the cache
    :return:
    """
    return Response("Not implemented", status=200, mimetype=resp_typ)


if __name__ == '__main__':
    app.cache = {}
    app.keys_to_expire = set()
    print("Starting Server --> localhost:%s"%port)
    app.run(port=port, debug=True)
