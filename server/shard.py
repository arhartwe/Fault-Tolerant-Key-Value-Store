from flask import Flask, json, jsonify, make_response, request, Blueprint
from collections import Counter
import vars
import os, sys, time, requests
headers = {'Content-Type': 'application/json'}   


shard_api = Blueprint('shard_api', __name__)

@shard_api.route("/key-value-store-shard/shard-ids", methods=['GET'])
def shard_id():
    if request.method == 'GET':
        response = {}
        response['message'] = "Shard IDs retrieved successfully"
        response['shard-ids'] = vars.shard_id_list
        return make_response(response, 200)
    else:
        pass

@shard_api.route("/key-value-store-shard/node-shard-id", methods=['GET'])
def node_shard_id():
    if request.method == 'GET':
        response = {}
        response['message'] = "Shard ID of the node retrieved successfully"
        response['shard-id'] = vars.shard_id
        return make_response(response, 200)
    else:
        pass

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
    count = len(node_keys) - 1
    ans = {"message":"Key count of shard ID retrieved successfully","shard-id-key-count":count}
    return make_response(jsonify(ans), 200)

@shard_api.route("/key-value-store-shard/shard-id-members/<shardID>", methods = ['GET'])
def shard_members(shardID):
    if request.method == 'GET':
        response = {}
        if int(shardID) >= vars.shard_count or int(shardID) < 0:
            response["Message"] = "Invalid shardID"
            return make_response(response, 400)
        else:
            response["Message"] = "Members of the shard ID retrieved successfully"
            response["shard-id-members"] = vars.shard_list[int(shardID)]
            return make_response(response, 200)
                 
    else:
        response = {}
        response['message'] = "Invalid Method"
        return make_response(response, 400)

@shard_api.route("/key-value-store-shard/update-member", methods = ['PUT'])
def update():
    data = request.get_json()
    
    vars.shard_count = data["shard-count"]
    vars.shard_id = int(data["shardID"])

    return make_response("", 200)

@shard_api.route("/key-value-store-shard/add-causal-member", methods = ['PUT'])
def add_member_helper():
    dataJson = request.get_json()
    new_replica = dataJson["socket-address"]

    vars.local_clock[new_replica] = 0
    return make_response("", 200)

@shard_api.route("/key-value-store-shard/get-shard-list", methods = ['GET'])
def get_shard_list():
    return jsonify({"shard-list":vars.shard_list})

@shard_api.route("/key-value-store-shard/get-shard-count", methods = ['GET'])
def get_shard_count():
    return jsonify({"Get-Shard-Count shard_count":vars.shard_count, "shardID":vars.shard_id})

@shard_api.route("/key-value-store-shard/add-member/<shardID>", methods = ['PUT'])
def add_shard_member(shardID):
    # NOTE: To add a new node to the store, we start the corresponding Docker container WITHOUT the SHARD_COUNT environment variable

    # This function will do the following things:
        # Update the shard count of the new node
        # Add the socket-address of the new node to everyone's view list and shard list
        # Add the socket-address of the new node to everyone's causal-metadata
        # Grab the KVS from a replica in the correct shard, as well as the causal-metadata

    data = request.get_json()
    shardID = int(shardID) - 1
    new_replica = data["socket-address"]
    #1 Update shard count, shardID of new node

    url = "http://" + new_replica + "/key-value-store-shard/update-member"
    resp = {"shard-count": vars.shard_count, "shardID": shardID}
    requests.put(url, headers = headers, json=resp)

    #2 Broadcast the socket-address of the new node to everyone's view list and shard list
    for replica in vars.view_list:
        if replica != new_replica:
            url = "http://" + replica + "/key-value-store/add-node"
            try:
                test = {'socket-address':new_replica, 'shardID': shardID}
                requests.put(url, json=test, headers=headers)
            except:
                pass

    #3 Add the node to causal metadata of correct shard
    for node in vars.shard_list[shardID]:
        if node != new_replica:
            url = "http://" + node + "/key-value-store-shard/add-causal-member"
            data = {'socket-address':new_replica}
            try:
                requests.put(url, json=data, headers=headers)
            except:
                pass
    
    #4 Update the new replica with the rest of the information from the correct shard
    if vars.shard_id == shardID:
        url = "http://" + new_replica + "/key-value-store/update-self"
        msg = {"key-store": vars.key_store, "causal-metadata":vars.local_clock}
        requests.put(url, json=msg, headers=headers, timeout = 5)
    else:
        data = {}
        for each in vars.shard_list[shardID]:
            if each != new_replica:
                url = "http://" + each + "/get-kvs"
                try:
                    resp = requests.get(url, headers=headers, timeout=5)
                    if resp.status_code == 200:
                        respJson = resp.json()
                        data = {"key-store":respJson['kvs'], "causal-metadata":respJson['causal-metadata']}
                        break
                except:
                    pass
        if not dict:
            print("KVS retrieval fail", file = sys.stderr)
            exit(1)
        
        url = "http://" + new_replica + "/key-value-store/update-self"
        requests.put(url, headers = headers, json=data, timeout = 5)

    msg = ""
    return make_response(msg,200)
    

    # print("key-value-store\n\n", file = sys.stderr)
    # print(new_replica, file=sys.stderr)
    # print("\n\n", file = sys.stderr)