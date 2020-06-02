from flask import Flask, json, jsonify, make_response, request, Blueprint
from collections import Counter
from clock import *
from kvs import *
from view import *
import vars
import os, sys, time, requests
import hashlib
headers = {'Content-Type': 'application/json'}    


server_api = Blueprint('server_api', __name__)

@server_api.route('/get-kvs', methods=['GET'])
def get_kvs():
    return jsonify({"kvs": vars.key_store, "causal-metadata":vars.local_clock})

@server_api.route('/get-local-clock', methods = ['GET'])
def get_local_clock():
    return jsonify({"Local Clock":vars.local_clock})

# Updates the KVS, clock, shard-count, view 
@server_api.route('/key-value-store/update-self', methods = ['PUT'])
def receive_kvs():
    data = request.get_json()

    vars.key_store = data["key-store"]
    vars.local_clock = data["causal-metadata"]

    vars.view_list.remove(vars.socket_address)
    vars.replication = len(vars.view_list) // vars.shard_count
    vars.shard_list = [vars.view_list[i:i+vars.replication] for i in range(0, len(vars.view_list), vars.replication)]
    vars.shard_id_list = [i for i in range(0, len(vars.shard_list))]
    
    vars.local_shard = vars.shard_list[vars.shard_id]
    
    vars.view_list.append(vars.socket_address)
    vars.local_shard.append(vars.socket_address)

    return make_response("", 200)


@server_api.route('/key-value-store/add-node', methods = ['PUT'])
def add_node():
    dataJson = request.get_json()
    new_socket = dataJson["socket-address"]
    shardID = dataJson["shardID"]

    vars.view_list.append(new_socket)
    vars.shard_list[int(shardID)].append(new_socket)

    return make_response("", 200)

@server_api.route('/key-value-store/<key>', methods=['PUT', 'GET', 'DELETE'])
def main_inst(key):
    key_hash = (hashlib.sha1(key.encode('utf8'))).hexdigest()
    if request.method == 'PUT' or request.method == 'DELETE':
    
        # Initialize incoming data
        data = request.get_json()
        meta_data = data['causal-metadata']
        sender_socket = request.remote_addr + ":8085"
        put_req = request.method == 'PUT'
        del_req = request.method == 'DELETE'
        resp = {}
        status = 500
        key_shard_id = int(key_hash, 16) % vars.shard_count

        # print ("Causal-metadata " + str(meta_data) + "\n", file = sys.stderr)
        # print ("Value " + str(data['value']) + "\n", file = sys.stderr)

        if key_shard_id != vars.shard_id:
            new_shard_list = vars.shard_list[key_shard_id]
            # Broadcast to node in correct shard the key
            response = ""
            resp_status = []
            for node in new_shard_list:
                url = "http://" + node + "/key-value-store/" + key
                try:
                    if put_req:
                        data = {"causal-metadata":meta_data, "value":data['value']}
                        response = requests.put(url, json = data, headers=headers)
                        # resp_status.append(response.status_code)
                        # print ("URL " + str(url) + "\n", file = sys.stderr)
                        if response.status_code == 400 or response.status_code == 501:
                            print("Error on line 84, server.py", file = sys.stderr)
                            exit(1)
                    elif del_req:
                        response = requests.delete(url, data=data, headers=headers)
                except:
                    pass
            response = response.json()
            test = {"causal-metadata":response["causal-metadata"], "shard-id":key_shard_id}
            if resp_status.count(201) == len(resp_status):
                return make_response(test, 201)
            else:
                return make_response(test, 200) 
        else:
            pass # Go ahead and continue as normal 

        # print ("Key Shard ID equals vars.shard_id\n", file = sys.stderr)
        # Check if metadata holds a vector clock, and replica socket is not in the metadata.
        if type(meta_data) is not str and vars.socket_address not in meta_data.keys():           
            print("\nNot supposed to be in here\n" , file=sys.stderr )
            # Add this replica back to the metadata and update our vector clock
            meta_data[vars.socket_address] = vars.local_clock[vars.socket_address]
            vars.local_clock = meta_data
            kvs_startup() # Get a new kvs and tell other replicas to add this replica to the view
            
        # print ("Metadata does hold a vector clock\n", file = sys.stderr)
        if compare_clocks(vars.view_list, meta_data, vars.local_clock, sender_socket):
            if put_req:
                resp, status = kvs_put(key, request, vars.key_store)
            else:
                resp, status = kvs_delete(key, vars.key_store)
            # print("\n\nResp " + str(resp) + "\n\nStatus" + str(status) + "\n\n", file=sys.stderr)
            # If the message is from the client - Increment our local clock and broadcast to other replicas. 
            if sender_socket not in vars.view_list:
                vars.local_clock[vars.socket_address] += 1
                broadcast_kvs(vars.local_shard, vars.socket_address, vars.local_clock, key, sender_socket) # broadcast with my local clock
            else: # Message is from another replica and we just increment the sender address.
                vars.local_clock[sender_socket] += 1
        
        # Go through the vars.queue and deliver any message that fulfils requirements.  
        else:
            # print ("At Line 117\n", file = sys.stderr)
            req = request
            vars.queue.append((meta_data, request))
            for clock, req in vars.queue:
                request_sender_socket = req.remote_addr + ":8085"
                
                if compare_clocks(vars.view_list, clock, vars.local_clock, request_sender_socket):
                    if put_req:
                        resp, status = kvs_put(key, req, vars.key_store)
                    else:
                        resp, status = kvs_delete(key, vars.key_store)
                    
                    vars.queue.remove((clock, req))
                    if request_sender_socket not in vars.view_list:
                        vars.local_clock[vars.socket_address] += 1
                        broadcast_kvs(vars.view_list, vars.socket_address, vars.local_clock, key, sender_socket) # broadcast with my local clock

                
        resp["causal-metadata"] = vars.local_clock
        return make_response(resp, status)

    elif request.method == 'GET':
        # 1) find out which shard the key belongs to
        key_hash_shard_id = int(key_hash, 16) % vars.shard_count
        # 2) Check if key belongs in your shard
        if key_hash_shard_id == vars.shard_id:
            if key in vars.key_store:
                value = vars.key_store[key]
                ans = {"message":"Retrieved successfully", "causal-metadata": vars.local_clock, "value": value}
                return make_response(ans, 200)
            else:
                ans = {"doesExist": False, "error": "Key does not exist",
                    "message": "Error in GET", "causal-metadata": vars.local_clock}
                return make_response(ans, 404)
        else:
            # 3) Send a get request to the correct shard
            correctShard = vars.shard_list[key_hash_shard_id]

            url = "http://" + correctShard[0] + "/key-value-store/" + key
            resp = requests.get(url, headers = headers, timeout = 5)
            respJson = resp.json()
            value  = respJson["value"]
            meta_data = respJson["causal-metadata"]
            ans = {"message":"Retrieved successfully", "causal-metadata": meta_data, "value":value}
            return make_response(ans, 200)
            # if resp.status_code == 200:
            #     ans = {"message":"Retrieved successfully", "causal-metadata": respJson["causal-metadata"], "value":respJson["value"]}
            #     return make_response(jsonify(ans), 200)
            # else:
            #     ans = {"doesExist": False, "error": "Key does not exist",
            #         "message": "Error in GET", "causal-metadata": respJson["causal-metadata"]}
            #     return make_response(jsonify(ans), 405)
    else:
        return "Fail"

@server_api.route('/key-value-store-view', methods=['PUT', 'GET', 'DELETE'])
def replica():
    if request.method == 'GET':
        resp = {"message": "view retrieved successfully",
                "view": ','.join(vars.view_list)}
        status = 200
        return make_response(jsonify(resp), status)

    if request.method == 'PUT':
        data = request.get_json()
        new_socket = data['socket-address']

        # if current socket is new socket, update KVS
        if new_socket == vars.socket_address:
            try:
                vars.key_store = data['dictionary']
            except:
                pass
        
        if new_socket not in vars.view_list:

            vars.view_list.append(new_socket)
            os.environ['VIEW'] = ','.join(vars.view_list)

            broadcast_view(vars.view_list)

            try:
                update_url = 'http://' + new_socket + '/key-value-store-view'
                requests.put(update_url, data={'dictionary':vars.key_store, 'socket-address':new_socket}, headers=headers)
            except:
                pass
    
            succ_message = {
                "message": "Replica added successfully to the vars.view"}
            return make_response(jsonify(succ_message), 201)

        else:
            error_message = {
                "error": "Socket address already exists in the view", "message": "Error in PUT"}
            return make_response(jsonify(error_message), 404)

    if request.method == 'DELETE':
        data = request.get_json()
        del_socket = data['socket-address']

        if del_socket in vars.view_list:
            try:
                vars.view_list.remove(del_socket)
                os.environ['VIEW'] = ','.join(vars.view_list)
                del vars.local_clock[del_socket]
            except:
                error_message = {
                    "error": "Socket address does not exist in the view", "message": "Error in DELETE"}
                return make_response(jsonify(error_message), 404)

            broadcast_view(vars.view_list)
                            
            try:
                url = 'http://' + del_socket + '/key-value-store-view'
                requests.delete(url, data=request.get_data(),
                            headers=headers, timeout=5)
            except: 
                pass
            
            succ_message = {
                "message": "Replica deleted successfully from the view"}
            return make_response(jsonify(succ_message), 200)


        else:
            error_message = {
                "error": "Socket address does not exist in the vars.view", "message": "Error in DELETE"}
            return make_response(jsonify(error_message), 404)
    
