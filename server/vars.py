from collections import Counter
import sys, os, math

# Replica values
view = os.environ.get('VIEW')
socket_address = os.environ.get('SOCKET_ADDRESS')
num_shards = os.environ.get('SHARD_COUNT')
headers = {'Content-Type': 'application/json'}    

# Replica objects
key_store = {"init": 0}
local_clock = Counter()
view_list = view.split(',')
queue = []
shard_list = [view_list[i:i+(len(view_list)//int(num_shards))] for i in range(0, len(view_list), (len(view_list)//int(num_shards)))]

for each in view_list:
    local_clock[each] = 0