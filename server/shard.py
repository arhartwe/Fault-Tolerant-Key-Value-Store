from flask import Flask, json, jsonify, make_response, request, Blueprint
from collections import Counter
from clock import *
from kvs import *
from view import *
import vars
import os, sys, time, requests
headers = {'Content-Type': 'application/json'}   


shard_api = Blueprint('shard_api', __name__)

@shard_api.route("/key-value-store-shard")
def placeholder():
    print("Hello")

@shard_api.route('/key-value-store-shard/shard-id-key-count/<shardID>', methods=['GET']) #is it okay if i change this endpoint to shardid?
def key_count(shardID):
    # for a given shard id, get nodes belonging to this shard id
    try:
        node_list = vars.shard_list[int(shardID)]
    except:
        ans = {"message":"Invalid shard ID"}
        return make_response(jsonify(ans), 400)

    # get key-store of 1 node from that shard
    node = node_list[0]
    url = 'http://' + node + '/get-kvs'
    resp = requests.get(url, headers=headers)
    node_keys = (resp.json())["kvs"]

    # Every node in a shard should have same # of items in kvs, so kvs * nodes in shard gives total key count
    count = (len(node_keys) * len(node_list)) - len(node_list) # len(node_list) because we initialize kvs with 1 key.
    ans = {"message":"Key count of shard ID retrieved successfully","shard-id-key-count":count}
    return make_response(jsonify(ans), 200)



