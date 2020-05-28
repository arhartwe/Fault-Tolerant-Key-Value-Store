from flask import Flask, json, jsonify, make_response, request, Blueprint
from collections import Counter
import vars
import os, sys, time, requests
headers = {'Content-Type': 'application/json'} 

shard_api = Blueprint('shard_api', __name__)

@shard_api.route("/key-value-store-shard/shard-id-members/<shardID>", methods = ['GET'])
def shard_members(shardID):
    if request.method == 'GET':
        response = {}
        if int(shardID) >= vars.shard_count or int(shardID) < 0:
            response["Message"] = "Invalid shardID"
            return make_response(response, 400)
        else:
            response["Message"] = "Members of the shard ID retrieved successfully"
            response["shard-id-members"] = vars.shard_list[shardID]
            return make_response(response, 200)
                 
    else:
        response = {}
        response['message'] = "Invalid Method"
        return make_response(response, 400)
