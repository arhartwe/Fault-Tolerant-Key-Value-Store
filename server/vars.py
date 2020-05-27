from collections import Counter
import sys, os

# Replica values
view = os.environ.get('VIEW')
socket_address = os.environ.get('SOCKET_ADDRESS')
replica_id = socket_address
headers = {'Content-Type': 'application/json'}    
shard_count = int(os.environ.get('SHARD_COUNT'))

# Replica objects
key_store = {"init": 0}
local_clock = Counter()
view_list = view.split(',')
queue = []
replication = len(view_list) // shard_count
shard_list = [view_list[i:i+replication] for i in range(0, len(view_list), replication)]
shard_ids = [i for i in range(0, len(shard_list))] 
for each in view_list:
    local_clock[each] = 0