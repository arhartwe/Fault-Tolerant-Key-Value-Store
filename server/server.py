from flask import Flask, json, jsonify, make_response, request
from collections import Counter
from clock import *
from kvs import *
from view import *
import vars

import os, sys, time, requests

app = Flask(__name__)

key_store = {"init": 0}
local_clock = Counter()
socket_address = os.environ.get('SOCKET_ADDRESS')
socket_ip = socket_ip = socket_address.split(':')[0]

view = os.environ.get('VIEW')
view_list = view.split(',')
view_socket_address = []
for each in view_list:
    view_socket_address.append(each.split(':')[0])
    local_clock[each] = 0

headers = {'Content-Type': 'application/json'}    
queue = []

@app.route('/get-kvs', methods=['GET'])
def get_kvs():
    return jsonify({"kvs": key_store})

@app.route('/key-value-store/<key>', methods=['PUT', 'GET', 'DELETE'])
def main_inst(key):

    if request.method == 'PUT' or request.method == 'DELETE':
        data = request.get_json()
        meta_data = data['causal-metadata']
        sender_socket = request.remote_addr + ":8085"
        put_req = request.method == 'PUT'
        queue_success = False
        resp = {}
        status = 500
        global local_clock
        global key_store

        if type(meta_data) is not str and socket_address not in meta_data.keys():
            url = "http://" + view_list[0] + "/get-kvs"
            try:
                response = requests.get(url, headers=headers)
                key_store = (response.json())["kvs"]
            except (requests.exceptions.ConnectionError):
                pass
            meta_data[socket_address] = local_clock[socket_address]
            local_clock = meta_data
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

            if sender_socket not in view_list:
                local_clock[socket_address] += 1
                broadcast_kvs(view_list, socket_address, local_clock, key, sender_socket) # broadcast with my local clock
            else:
                local_clock[sender_socket] += 1
            
        else:
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
                    queue_success = True

            if not queue_success:
                queue.append((meta_data, request))
                
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

def main():
    try:
        for each in view_list:
            if socket_address != each:
                update_url = 'http://' + each + '/key-value-store-view'
                requests.put(update_url, json={'socket-address': socket_address}, headers=headers)
                resp = requests.get("http://" + each + "/get-kvs",headers=headers)
                global key_store
                key_store = (resp.json())["kvs"]
    except:
        pass
    app.run(debug=True, host='0.0.0.0', port=8085)

if __name__ == '__main__':
    main()
    