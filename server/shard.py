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

@shard_api.route('/key-value-store-shard/deleteallkvs/<count>', methods=['DELETE'])
def delete_all(count):
    if request.method == 'DELETE':
        try:
            # Store new shard count value in environment variable
            new_shard_count = int(count)
            vars.shard_count = new_shard_count
            os.environ['SHARD_COUNT'] = str(new_shard_count)

            # Reshard the nodes according to new shard value
            for index in range(0, len(view_list)):
                vars.shard_list[index % new_shard_count] = view_list[index]
            vars.shard_id_list = [i for i in range(0, len(vars.shard_list))]

            # Index nodes according to new shard value
            vars.local_shard = []
            shard_id = -1
            for shard in vars.shard_list:
                if vars.replica_id in shard:
                    shard_id = vars.shard_list.index(shard)
                    vars.local_shard = shard

            vars.key_store = {}
            response = {}
            response['message'] = "Resharding done successfully"
            return make_response(response, 200) 
        except:
            response = {}
            response['message'] = "Unable to access SHARD_COUNT environment variable"
            return make_response(response, 400)

    else:
        response = {}
        response['message'] = "This endpoint only handles deletes"
        return make_response(response, 400) 

@shard_api.route('/key-value-store-shard/reshard', methods=['PUT'])
def reshard():
    # 1. check if 2 nodes per shard is possible
    # 2. create 1 large kvs from all kvs stores
    # 3. delete all kvs of all nodes? 
    #    -> new endpoint that sets kvs to empty? kvs = {}
    #    -> broadcast this to every node
    # 4. Redestribute keys based on new shard value (for all keys, send PUT request)
       
    if request.method == 'PUT':
        data = request.get_json()
        new_shards = data['shard-count']
        node_count = len(vars.view_list)

        # if the shards can't be distributed so that one isn't left over OR
        # if there are not at least 2x nodes as shards 
        if new_shards > node_count or new_shards * 2 > node_count:
            response = {}
            response['message'] = "Not enough nodes to provide fault-tolerance with the given shard count!"
            return make_response(response, 400)
        else:
            # Create a new kvs that will hold all keys across all shards
            reshard_kvs = {}
            for shards in vars.shard_list:
                # Get all keys across all shards and update single large kvs
                try:
                    resp = requests.get("http://" + shards[0] + "/get-kvs",headers=headers)
                    temp_store = {}
                    temp_store = (resp.json())["kvs"]
                    reshard_kvs.update(temp_store)
                except:
                    response = {}
                    response['message'] = "Unable to create one large kvs for resharding"
                    return make_response(response, 401)

                # For every node in every shard, delete the current kvs 
                for nodes in shards:
                        url = "http://" + nodes + "/key-value-store-shard/deleteallkvs/" + str(new_shards)
                        print(url, file=sys.stderr)
                        requests.delete(url, headers=headers)

        # For every key in the new compounded kvs, resdistributed keys (this can be optimized better)
        for key in reshard_kvs:
            url = "http://" + vars.view_list[0] + "/key-value-store/" + key
            print(url, file=sys.stderr)
            requests.put(url, data=data, headers=headers)

        response = {}
        response['message'] = "Resharding done successfully"
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
    data = request.get_json()
    shardID = int(shardID)
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
