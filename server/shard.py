from flask import Flask, json, jsonify, make_response, request, Blueprint
from collections import Counter
from clock import *
from kvs import *
from view import *
import vars
import os, sys, time, requests
headers = {'Content-Type': 'application/json'}   


shard_api = Blueprint('shard_api', __name__)

@shard_api.route("/key-value-store-shard/shard-ids", methods=['GET'])
def shard_id():
    if request.method == 'GET':
        response = {}
        response['message'] = "Shard IDs retrieved successfully"
        response['shard-ids'] = vars.shard_ids
        return make_response(response, 200)

#@shard_api.route("/key-value-store-shard/node-shard-id")
