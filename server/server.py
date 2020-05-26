from flask import Flask, json, jsonify, make_response, request
from collections import Counter
from clock import *
from kvs import *
from view import *
from main import app, socket_address, view, view_list, local_clock, queue 
import os, sys, time, requests


@app.route('/get-kvs', methods=['GET'])
def get_kvs():
    return jsonify({"kvs": key_store})

@app.route('/key-value-store/<key>', methods=['PUT', 'GET', 'DELETE'])
def main_inst(key):

    if request.method == 'PUT' or request.method == 'DELETE':
        
        # Initialize incoming data
        data = request.get_json()
        meta_data = data['causal-metadata']
        sender_socket = request.remote_addr + ":8085"
        put_req = request.method == 'PUT'
        queue_success = False
        resp = {}
        status = 500
        global local_clock
        global key_store

        # Check if metadata holds a vector clock, and replica socket is not in the metadata.
        # Verifies that this replica has recently gone down and may have missed data.
        # TODO: Change view_list[0] to something else incase this replica is view_list[0] 
        if type(meta_data) is not str and socket_address not in meta_data.keys():
            url = "http://" + view_list[0] + "/get-kvs"
            # Get a KVS from another replica. In this case get it from view_list[0]
            try:
                response = requests.get(url, headers=headers)
                key_store = (response.json())["kvs"]
            except (requests.exceptions.ConnectionError):
                pass
            
            # Add this replica back to the metadata and update our vector clock
            meta_data[socket_address] = local_clock[socket_address]
            local_clock = meta_data
            
            # Tell other replicas to put this replica back in the view. 
            for replica in view_list:
                if replica != socket_address:
                    try:
                        url = "http://" + replica + "/key-value-store-view"
                        requests.put(url, json={'socket-address': socket_address}, headers=headers)
                    except Exception as e:
                        print(e, file=sys.stderr)
                    

        if compare_clocks(view_list, meta_data, local_clock, sender_socket):
            
            if put_req:
                resp, status = kvs_put(key, request, key_store)
            else:
                resp, status = kvs_delete(key, key_store)
            
            # If the message is from the client - Increment our local clock and broadcast to other replicas. 
            if sender_socket not in view_list:
                local_clock[socket_address] += 1
                broadcast_kvs(view_list, socket_address, local_clock, key, sender_socket) # broadcast with my local clock
            else: # Message is from another replica and we just increment the sender address.
                local_clock[sender_socket] += 1
        
        # Go through the queue and deliver any message that fulfils requirements.  
        else:
            req = request
            queue.append((meta_data, request))
            for clock, req in queue:
                request_sender_socket = req.remote_addr + ":8085"
                
                if compare_clocks(view_list, clock, local_clock, request_sender_socket):
                    if put_req:
                        resp, status = kvs_put(key, req, key_store)
                    else:
                        resp, status = kvs_delete(key, key_store)
                    
                    queue.remove((clock, req))
                    if request_sender_socket not in view_list:
                        local_clock[socket_address] += 1
                        broadcast_kvs(view_list, socket_address, local_clock, key, sender_socket) # broadcast with my local clock

                
        resp["causal-metadata"] = local_clock
        return make_response(resp, status)

    elif request.method == 'GET':
        if key in key_store:
            value = key_store[key]
            ans = {"message":"Retrieved successfully", "causal-metadata": local_clock, "value": value}
            return make_response(jsonify(ans), 200)
        else:
            ans = {"doesExist": False, "error": "Key does not exist",
                   "message": "Error in GET", "causal-metadata": local_clock}
            return make_response(jsonify(ans), 404)

    else:
        return "Fail"

@app.route('/key-value-store-view', methods=['PUT', 'GET', 'DELETE'])
def replica():
    if request.method == 'GET':
        resp = {"message": "View retrieved successfully",
                "view": ','.join(view_list)}
        status = 200
        return make_response(jsonify(resp), status)

    if request.method == 'PUT':
        data = request.get_json()
        new_socket = data['socket-address']

        # if current socket is new socket, update KVS
        if new_socket == socket_address:
            try:
                key_store = data['dictionary']
            except:
                pass
        
        if new_socket not in view_list:

            view_list.append(new_socket)
            os.environ['VIEW'] = ','.join(view_list)

            broadcast_view(view_list)

            try:
                update_url = 'http://' + new_socket + '/key-value-store-view'
                requests.put(update_url, data={'dictionary':key_store, 'socket-address':new_socket}, headers=headers)
            except:
                pass
    
            succ_message = {
                "message": "Replica added successfully to the view"}
            return make_response(jsonify(succ_message), 201)

        else:
            error_message = {
                "error": "Socket address already exists in the view", "message": "Error in PUT"}
            return make_response(jsonify(error_message), 404)

    if request.method == 'DELETE':
        data = request.get_json()
        del_socket = data['socket-address']


        if del_socket in view_list:
            try:
                view_list.remove(del_socket)
                os.environ['VIEW'] = ','.join(view_list)
                del local_clock[del_socket]
            except:
                error_message = {
                    "error": "Socket address does not exist in the view", "message": "Error in DELETE"}
                return make_response(jsonify(error_message), 404)

            broadcast_view(view_list)
                            
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
                "error": "Socket address does not exist in the view", "message": "Error in DELETE"}
            return make_response(jsonify(error_message), 404)
    