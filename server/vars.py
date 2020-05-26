from collections import Counter
import sys, os

# Replica values
view = os.environ.get('VIEW')
socket_address = os.environ.get('SOCKET_ADDRESS')
headers = {'Content-Type': 'application/json'}    

# Replica objects
key_store = {"init": 0}
local_clock = Counter()
view_list = view.split(',')
queue = []
for each in view_list:
    local_clock[each] = 0