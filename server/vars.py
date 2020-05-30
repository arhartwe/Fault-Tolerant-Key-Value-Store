from collections import Counter
import sys, os, math
import hashlib

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
for each in view_list:
    local_clock[each] = 0

# Shard values and objects
replication = len(view_list) // shard_count
shard_list = [view_list[i:i+replication] for i in range(0, len(view_list), replication)]
shard_id_list = [i for i in range(0, len(shard_list))]
local_shard = [] 

shard_id = -1
for shard in shard_list:
    if replica_id in shard:
        shard_id = shard_list.index(shard)
        local_shard = shard
        string = "value"

# shard_list = [[0,1,2], [4,5,6]]
# shard_id_list = [0,1]
# shard_id = 0
