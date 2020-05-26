from flask import Flask, json, jsonify, make_response, request, Blueprint
from collections import Counter
from clock import *
from kvs import *
from view import *
import vars
import os, sys, time, requests

server_api = Blueprint('server_api', __name__)

@server_api.route('/get-kvs', methods=['GET'])
def get_kvs():
    return jsonify({"kvs": vars.key_store})

@server_api.route('/key-value-store/<key>', methods=['PUT', 'GET', 'DELETE'])
def main_inst(key):

    if request.method == 'PUT' or request.method == 'DELETE':
        
        # Initialize incoming data
        data = request.get_json()
        meta_data = data['causal-metadata']
        sender_socket = request.remote_addr + ":8085"
        put_req = request.method == 'PUT'
        resp = {}
        status = 500

        # Check if metadata holds a vector clock, and replica socket is not in the metadata.
        # Verifies that this replica has recently gone down and may have missed data.
        # TODO: Change vars.view_list[0] to something else incase this replica is vars.view_list[0] 
        if type(meta_data) is not str and vars.socket_address not in meta_data.keys():
            url = "http://" + vars.view_list[0] + "/get-kvs"
            # Get a KVS from another replica. In this case get it from vars.view_list[0]
            try:
                response = requests.get(url, headers=headers)
                vars.key_store = (response.json())["kvs"]
            except (requests.exceptions.ConnectionError):
                pass
            
            # Add this replica back to the metadata and update our vector clock
            meta_data[vars.socket_address] = vars.local_clock[vars.socket_address]
            vars.local_clock = meta_data
            
            # Tell other replicas to put this replica back in the vars.view. 
            for replica in vars.view_list:
                if replica != vars.socket_address:
                    try:
                        url = "http://" + replica + "/key-value-store-vars.view"
                        requests.put(url, json={'socket-address': vars.socket_address}, headers=headers)
                    except Exception as e:
                        print(e, file=sys.stderr)
                    

        if compare_clocks(vars.view_list, meta_data, vars.local_clock, sender_socket):
            
            if put_req:
                resp, status = kvs_put(key, request, vars.key_store)
            else:
                resp, status = kvs_delete(key, vars.key_store)
            
            # If the message is from the client - Increment our local clock and broadcast to other replicas. 
            if sender_socket not in vars.view_list:
                vars.local_clock[vars.socket_address] += 1
                broadcast_kvs(vars.view_list, vars.socket_address, vars.local_clock, key, sender_socket) # broadcast with my local clock
            else: # Message is from another replica and we just increment the sender address.
                vars.local_clock[sender_socket] += 1
        
        # Go through the vars.queue and deliver any message that fulfils requirements.  
        else:
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
        if key in vars.key_store:
            value = vars.key_store[key]
            ans = {"message":"Retrieved successfully", "causal-metadata": vars.local_clock, "value": value}
            return make_response(jsonify(ans), 200)
        else:
            ans = {"doesExist": False, "error": "Key does not exist",
                   "message": "Error in GET", "causal-metadata": vars.local_clock}
            return make_response(jsonify(ans), 404)

    else:
        return "Fail"

@server_api.route('/key-value-store-view', methods=['PUT', 'GET', 'DELETE'])
def replica():
    if request.method == 'GET':
        resp = {"message": "vars.view retrieved successfully",
                "vars.view": ','.join(vars.view_list)}
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
            os.environ['vars.view'] = ','.join(vars.view_list)

            broadcast_view(vars.view_list)

            try:
                update_url = 'http://' + new_socket + '/key-value-store-vars.view'
                requests.put(update_url, data={'dictionary':vars.key_store, 'socket-address':new_socket}, headers=headers)
            except:
                pass
    
            succ_message = {
                "message": "Replica added successfully to the vars.view"}
            return make_response(jsonify(succ_message), 201)

        else:
            error_message = {
                "error": "Socket address already exists in the vars.view", "message": "Error in PUT"}
            return make_response(jsonify(error_message), 404)

    if request.method == 'DELETE':
        data = request.get_json()
        del_socket = data['socket-address']


        if del_socket in vars.view_list:
            try:
                vars.view_list.remove(del_socket)
                os.environ['vars.view'] = ','.join(vars.view_list)
                del vars.local_clock[del_socket]
            except:
                error_message = {
                    "error": "Socket address does not exist in the vars.view", "message": "Error in DELETE"}
                return make_response(jsonify(error_message), 404)

            broadcast_view(vars.view_list)
                            
            try:
                url = 'http://' + del_socket + '/key-value-store-vars.view'
                requests.delete(url, data=request.get_data(),
                            headers=headers, timeout=5)
            except: 
                pass
            
            succ_message = {
                "message": "Replica deleted successfully from the vars.view"}
            return make_response(jsonify(succ_message), 200)


        else:
            error_message = {
                "error": "Socket address does not exist in the vars.view", "message": "Error in DELETE"}
            return make_response(jsonify(error_message), 404)
    