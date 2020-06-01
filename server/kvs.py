from flask import json, jsonify, make_response, request
from view import delete_replica_view
import vars
import requests 
import sys

headers = {'Content-Type': 'application/json'}  

# TODO: change view_list to local shard list
def broadcast_kvs(view_list, socket_address, local_clock, key, request_address):
    # Skip if request is from another replica
    if request_address not in view_list:
        for replica in view_list:
            if replica is not socket_address:
                url = 'http://' + replica + '/key-value-store/' + key
                try:
                    new_data = request.get_json()
                    new_data['causal-metadata'] = local_clock

                    if request.method == 'PUT':
                        requests.put(url, json=dict(new_data), headers=headers, timeout=5)
                    else:
                        requests.delete(url, json=dict(new_data), headers=headers, timeout=5)
                
                # Replica has crashed and needs to be removed from the view
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                    next_replica = view_list.index(replica) + 1
                    # Keep broadcasting to rest of nodes
                    broadcast_kvs(view_list[next_replica:], socket_address, local_clock, key, request_address)
                    # delete_replica_view(socket_address, replica)
def kvs_put(key, req, key_store):
    response = req.get_json()
    if 'value' not in response:
        resp = {"error": "Value is missing", "message": "Error in PUT"}
        return make_response(jsonify(resp), 400)

    elif len(key) > 50:
        resp = {"error": "Key is too long", "message": "Error in PUT"}
        return make_response(jsonify(resp), 400)
        
    else:
        val = response['value']
        resp = {}
        status = 501
        
        if key in key_store.keys():
            key_store[key] = val
            resp['message'] = "Updated successfully"
            status = 200
        else:
            key_store[key] = val 
            resp['message'] = "Added successfully"
            status = 201
        resp['shard-id'] = vars.shard_id 
        return resp, status

def kvs_delete(key, key_store):
    if key in key_store:
        del key_store[key]
        msg = {"doesExist": True, "message": "Deleted successfully"}
        return msg, 200
    else:
        msg = {"doesExist": False, "error": "Key does not exist",
                "message": "Error in DELETE"}
        return msg, 404

def kvs_startup():
    try:
        for each in vars.local_shard:
            if vars.socket_address != each:
                update_url = 'http://' + each + '/key-value-store-view'
                requests.put(update_url, json={'socket-address': vars.socket_address}, headers=headers)
                resp = requests.get("http://" + each + "/get-kvs",headers=headers)
                vars.key_store = (resp.json())["kvs"]
    except:
    # except Exception as e:
        # print(e, file=sys.stderr)  
        pass