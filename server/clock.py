from collections import Counter
import vars
import requests

headers = {'Content-Type': 'application/json'}    

def compare_clocks(view_list, meta_data, local_clock, sender_socket):
    # If the sender is the client then return true so that it still delivers
    return True
    # if sender_socket not in view_list or meta_data == "":
    #     return True
    # if meta_data[sender_socket] - 1 == local_clock[sender_socket]:
    #     for process in local_clock:
    #         if process == sender_socket:
    #             continue
    #         elif not meta_data[process] <= local_clock[process]:
    #             return False
    #     return True

    # else:
    #     return False

def broadcast_clock(socket_address, local_clock, shardID, sender_socket):
    for each in vars.shard_id_list:
        if each != shardID:
            for replica in vars.shard_list[each]:
                if replica != sender_socket:
                    url = 'http://' + replica + '/update-clock'
                    try:
                        clock = {"causal-metadata":vars.local_clock}
                        requests.put(url, json = clock, headers=headers)
                    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                        pass