from flask import Flask, json, jsonify, make_response, request, blueprints
from collections import Counter
import vars
from server import server_api
import os, sys, time, requests

app = Flask(__name__)
app.register_blueprint(server_api)

def main():
    try:
        for each in vars.view_list:
            if vars.socket_address != each:
                update_url = 'http://' + each + '/key-value-store-view'
                requests.put(update_url, json={'socket-address': vars.socket_address}, headers=headers)
                resp = requests.get("http://" + each + "/get-kvs",headers=headers)
                vars.key_store = (resp.json())["kvs"]
    except:
        pass    
    app.run(debug=True, host='0.0.0.0', port=8085)

if __name__ == '__main__':
    main()

    