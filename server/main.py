from flask import Flask, json, jsonify, make_response, request, blueprints
from collections import Counter
from kvs import kvs_startup
import vars
from server import server_api
from shard import shard_api
import os, sys, time, requests, math

app = Flask(__name__)
app.register_blueprint(server_api)
app.register_blueprint(shard_api)
headers = {'Content-Type': 'application/json'}    


def main():
    kvs_startup()
    app.run(debug=True, host='0.0.0.0', port=8085)

if __name__ == '__main__':
    main()

    