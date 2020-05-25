from flask import json, jsonify, make_response, request
import requests 
import sys

headers = {'Content-Type': 'application/json'}  

def delete_replica_view(socket_address, socket):
    url = 'http://' + socket_address + '/key-value-store-view'
    try:
        requests.delete(url, json={'socket-address': socket}, headers=headers)
    except:
        print("fail", file=sys.stderr)
        pass

def broadcast_view(view_list):
    for replica in view_list:
        url = 'http://' + replica + '/key-value-store-view'
        try:
            if request.method == 'PUT':
                requests.put(url, data=request.get_data(),
                            headers=headers, timeout=5)
            elif request.method == 'DELETE':
                requests.delete(url, data=request.get_data(),
                                headers=headers, timeout=5)

            # timeout means we need to delete that replica from the view
            # TODO: Choose timeout value
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            for del_replica in view_list:
                url = 'http://' + del_replica + '/key-value-store-view'
                try:
                    requests.delete(url, data={"socket-address": replica}, headers=headers, timeout=5)
                except:
                    pass