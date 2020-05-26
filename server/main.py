from flask import Flask, json, jsonify, make_response, request
from collections import Counter
import os, sys, time, requests


app = Flask(__name__)

# Replica values
view = os.environ.get('VIEW')
socket_address = os.environ.get('SOCKET_ADDRESS')
headers = {'Content-Type': 'application/json'}    

# Replica objects
key_store = {"init": 0}
local_clock = Counter()
view_list = view.split(',')
queue = []
for each in view_list:
    local_clock[each] = 0

# Get a keystore from another replica and tell other replicas to add me to the view
def init():
    try:
        for each in view_list:
            if socket_address != each:
                update_url = 'http://' + each + '/key-value-store-view'
                requests.put(update_url, json={'socket-address': socket_address}, headers=headers)
                resp = requests.get("http://" + each + "/get-kvs",headers=headers)
                global key_store
                key_store = (resp.json())["kvs"]
    except:
        pass

def main():
    init()
    app.run(debug=True, host='0.0.0.0', port=8085)

if __name__ == '__main__':
    main()

    