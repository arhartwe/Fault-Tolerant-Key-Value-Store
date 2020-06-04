import hashlib
key = "key0"

key_hash = (hashlib.sha1(key.encode('utf8'))).hexdigest()
key_hash_shard_id = int(key_hash, 16) % 2

print (key + " " + str(key_hash_shard_id))
