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

# @shard_api.route('/key-value-store-shard/shard-id-key-count/<shard-id>', methods=['GET'])
# def key_count():
#     # For every node in shard
#     #for every node in #shard variable:
            
#     # Get Key-Store from a node in a shard
#     # get count of keys in this dictionary
#     # count += number of keys
#     # return count
#     return# count




