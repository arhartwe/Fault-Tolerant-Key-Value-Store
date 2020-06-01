################### 
# Course: CSE138
# Date: Spring 2020
# Assignment: 4
# Authors: Reza NasiriGerdeh, Zach Gottesman, Lindsey Kuper
# This document is the copyrighted intellectual property of the authors.
# Do not copy or distribute in any form without explicit permission.
###################

import unittest
import requests
import time
import os

TIMEOUT=60

######################## initialize variables ################################################
subnetName = "assignment4-net"
subnetAddress = "10.10.0.0/16"

nodeIpList = ["10.10.0.2", "10.10.0.3", "10.10.0.4", "10.10.0.5", "10.10.0.6", "10.10.0.7"]
nodeHostPortList = ["8082","8083", "8084", "8086", "8087", "8088"]
nodeSocketAddressList = [ replicaIp + ":8085" for replicaIp in nodeIpList ]

view = ""
for nodeSocketAddress in nodeSocketAddressList:
    view += nodeSocketAddress + ","
view = view[:-1]

shardCount = 2

############################### Docker Linux Commands ###########################################################
def removeSubnet(subnetName):
    command = "docker network rm " + subnetName
    os.system(command)
    time.sleep(2)

def createSubnet(subnetAddress, subnetName):
    command  = "docker network create --subnet=" + subnetAddress + " " + subnetName
    os.system(command)
    time.sleep(2)

def buildDockerImage():
    command = "docker build -t assignment4-img ."
    os.system(command)

def runInstance(hostPort, ipAddress, subnetName, instanceName):
    command = "docker run -d -p " + hostPort + ":8085 --net=" + subnetName + " --ip=" + ipAddress + " --name=" + instanceName + " -e SOCKET_ADDRESS=" + ipAddress + ":8085" + " -e VIEW=" + view + " -e SHARD_COUNT=" + str(shardCount) + " assignment4-img"
    os.system(command)
    time.sleep(20)

def runAdditionalInstance(hostPort, ipAddress, subnetName, instanceName, newView):
    command = "docker run -d -p " + hostPort + ":8085 --net=" + subnetName + " --ip=" + ipAddress + " --name=" + instanceName + " -e SOCKET_ADDRESS=" + ipAddress + ":8085" + " -e VIEW=" + newView  + " assignment4-img"
    os.system(command)
    time.sleep(20)

def stopAndRemoveInstance(instanceName):
    stopCommand = "docker stop " + instanceName
    removeCommand = "docker rm " + instanceName
    os.system(stopCommand)
    time.sleep(2)
    os.system(removeCommand)

def connectToNetwork(subnetName, instanceName):
    command = "docker network connect " + subnetName + " " + instanceName
    os.system(command)

def disconnectFromNetwork(subnetName, instanceName):
    command = "docker network disconnect " + subnetName + " " + instanceName
    os.system(command)

############################### View Comparison Function ###########################################################
def compareViews(returnedView, expectedView):
    expectedView = expectedView.split(',')
    if (type(returnedView) is not list):
        returnedView = returnedView.split(',')
    else:
        returnedView = returnedView
    returnedView.sort()
    expectedView.sort()
    return returnedView == expectedView
############################### Array Comparison Function ###########################################################
def compareLists(list1, list2):
    list1.sort()
    list2.sort()
    return list1 == list2
################################# Unit Test Class ############################################################

class TestHW3(unittest.TestCase):

    shardIdList = []
    shardsMemberList = []
    keyCount = 600

    ######################## Build docker image and create subnet ################################
    print("###################### Building Docker Image ######################\n")
    # build docker image
    buildDockerImage()

    # stop and remove containers from possible previous runs
    print("\n###################### Stopping and removing containers from previous run ######################\n")
    stopAndRemoveInstance("node1")
    stopAndRemoveInstance("node2")
    stopAndRemoveInstance("node3")
    stopAndRemoveInstance("node4")
    stopAndRemoveInstance("node5")
    stopAndRemoveInstance("node6")
    stopAndRemoveInstance("node7")


    print("\n###################### Creating the subnet ######################\n")
    # remove the subnet possibly created from the previous run
    removeSubnet(subnetName)

    # create subnet
    createSubnet(subnetAddress, subnetName)

    # run instances
    print("\n###################### Running Instances ######################\n")
    runInstance(nodeHostPortList[0], nodeIpList[0], subnetName, "node1")
    runInstance(nodeHostPortList[1], nodeIpList[1], subnetName, "node2")
    runInstance(nodeHostPortList[2], nodeIpList[2], subnetName, "node3")
    runInstance(nodeHostPortList[3], nodeIpList[3], subnetName, "node4")
    runInstance(nodeHostPortList[4], nodeIpList[4], subnetName, "node5")
    runInstance(nodeHostPortList[5], nodeIpList[5], subnetName, "node6")

    print("\n###################### Running Tests ######################\n")

    ########################## Run tests #######################################################

    def test_a_get_shard_ids(self):
        time.sleep(10)

        print("\n###################### Getting Shard IDs ######################\n")

        # get the shard IDs from node1
        response = requests.get( 'http://localhost:8082/key-value-store-shard/shard-ids', timeout=TIMEOUT)
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)
        shardIdsFromNode1 = responseInJson['shard-ids']
        self.assertEqual(len(shardIdsFromNode1), shardCount)

        # get the shard IDs from node5
        response = requests.get( 'http://localhost:8087/key-value-store-shard/shard-ids', timeout=TIMEOUT)
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)
        shardIdsFromNode5 = responseInJson['shard-ids']
        self.assertTrue(compareLists(shardIdsFromNode5, shardIdsFromNode1))

        # get the shard IDs from node6
        response = requests.get( 'http://localhost:8088/key-value-store-shard/shard-ids', timeout=TIMEOUT)
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)
        shardIdsFromNode6 = responseInJson['shard-ids']
        self.assertTrue(compareLists(shardIdsFromNode6, shardIdsFromNode1))

        self.shardIdList += shardIdsFromNode1

    def test_b_shard_id_members(self):

        print("\n###################### Getting the Members of Shard IDs ######################\n")

        shard1 = str(self.shardIdList[0])
        shard2 = str(self.shardIdList[1])

        # get the members of shard1 from node2
        response = requests.get( 'http://localhost:8083/key-value-store-shard/shard-id-members/' + shard1, timeout=TIMEOUT)
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)
        shard1Members = responseInJson['shard-id-members']
        self.assertGreater(len(shard1Members), 1)

        # get the members of shard2 from node3
        response = requests.get( 'http://localhost:8084/key-value-store-shard/shard-id-members/' + shard2, timeout=TIMEOUT)
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)
        shard2Members = responseInJson['shard-id-members']
        self.assertGreater(len(shard2Members), 1)

        self.assertEqual(len(nodeSocketAddressList), len(shard1Members + shard2Members))

        self.shardsMemberList += [shard1Members]
        self.shardsMemberList += [shard2Members]


    def test_c_node_shard_id(self):

        print("\n###################### Getting the Shard ID of the nodes ######################\n")

        shard1 = self.shardIdList[0]

        # get the shard id of node1
        response = requests.get( 'http://localhost:8082/key-value-store-shard/node-shard-id', timeout=TIMEOUT)
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)

        node1ShardId = responseInJson['shard-id']

        self.assertTrue(node1ShardId in self.shardIdList)

        if node1ShardId == shard1:
            self.assertTrue(nodeSocketAddressList[0] in self.shardsMemberList[0])
        else:
            self.assertTrue(nodeSocketAddressList[0] in self.shardsMemberList[1])

        # get the shard id of node2
        response = requests.get('http://localhost:8083/key-value-store-shard/node-shard-id', timeout=TIMEOUT)
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)

        node2ShardId = responseInJson['shard-id']

        self.assertTrue(node2ShardId in self.shardIdList)

        if node2ShardId == shard1:
            self.assertTrue(nodeSocketAddressList[1] in self.shardsMemberList[0])
        else:
            self.assertTrue(nodeSocketAddressList[1] in self.shardsMemberList[1])


        # get the shard id of node6
        response = requests.get('http://localhost:8088/key-value-store-shard/node-shard-id', timeout=TIMEOUT)
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)

        node6ShardId = responseInJson['shard-id']

        self.assertTrue(node6ShardId in self.shardIdList)

        if node6ShardId == shard1:
            self.assertTrue(nodeSocketAddressList[5] in self.shardsMemberList[0])
        else:
            self.assertTrue(nodeSocketAddressList[5] in self.shardsMemberList[1])


    def test_d_put_key_value_operation(self):

        print("\n###################### Putting keys/values to the store ######################\nThis takes at least 10 minutes\n")
        nextCausalMetadata = ""

        for counter in range(self.keyCount):
            nodeIndex = counter % len(nodeIpList)

            # put a new key in the store
            response = requests.put('http://localhost:' + nodeHostPortList[nodeIndex] + '/key-value-store/key' + str(counter), json={'value': "value" + str(counter), "causal-metadata": nextCausalMetadata}, timeout=TIMEOUT)
            responseInJson = response.json()
            self.assertEqual(response.status_code, 201)
            nextCausalMetadata = responseInJson["causal-metadata"]

            keyShardId = responseInJson["shard-id"]

            self.assertTrue(keyShardId in self.shardIdList)

            time.sleep(1)

    def test_e_get_key_value_operation(self):

        time.sleep(10)

        print("\n###################### Getting keys/values from the store ######################\n")


        for counter in range(self.keyCount):

            nodeIndex = (counter + 1 ) % len(nodeIpList)

            # get the value of the key
            response = requests.get('http://localhost:' + nodeHostPortList[nodeIndex] + '/key-value-store/key' + str(counter), timeout=TIMEOUT)
            responseInJson = response.json()
            self.assertEqual(response.status_code, 200)
            value = responseInJson["value"]
            self.assertEqual(value, "value" + str(counter))

    def test_f_shard_key_count(self):

        print("\n###################### Getting key count of each shard ######################\n")

        shard1 = str(self.shardIdList[0])
        shard2 = str(self.shardIdList[1])

        # get the shard1 key count from node5
        response = requests.get( 'http://localhost:8087/key-value-store-shard/shard-id-key-count/' + shard1, timeout=TIMEOUT)
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)
        shard1KeyCount = int(responseInJson['shard-id-key-count'])

        # get the shard2 key count from node3
        response = requests.get( 'http://localhost:8084/key-value-store-shard/shard-id-key-count/' + shard2, timeout=TIMEOUT)
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)
        shard2KeyCount = int(responseInJson['shard-id-key-count'])

        # sum of key counts in shards == total keys
        self.assertEqual(self.keyCount, shard1KeyCount + shard2KeyCount)

        # check whether keys distributed almost uniformly
        minKeyCount = int ((self.keyCount * 0.75) / shardCount)
        maxKeyCount = int ((self.keyCount * 1.25) / shardCount)

        # minKeyCount < shard2-key-count < maxKeyCount
        self.assertGreater(shard1KeyCount, minKeyCount)
        self.assertLess(shard1KeyCount, maxKeyCount)

        # minKeyCount < shard2-key-count < maxKeyCount
        self.assertGreater(shard2KeyCount, minKeyCount)
        self.assertLess(shard2KeyCount, maxKeyCount)

    def test_g_add_new_node(self):

        shard2 = self.shardIdList[1]


        print("\n###################### Adding a new node ######################\n")
        node7Ip = "10.10.0.8"
        node7HostPort = "8089"
        node7SocketAddress = "10.10.0.8:8085"
        newView =  view + "," + node7SocketAddress

        runAdditionalInstance(node7HostPort, node7Ip, subnetName, "node7", newView)

        time.sleep(10)

        # get the new view from node1
        response = requests.get( 'http://localhost:8082/key-value-store-view', timeout=TIMEOUT)
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(compareViews(responseInJson['view'], newView))

        print("\n###################### Assigning the new node to the second shard ######################\n")

        response = requests.put('http://localhost:8082/key-value-store-shard/add-member/' + str(shard2), json={'socket-address': node7SocketAddress}, timeout=TIMEOUT)
        self.assertEqual(response.status_code, 200)

        time.sleep(5)

        # get the shard id of node7
        response = requests.get('http://localhost:8089/key-value-store-shard/node-shard-id', timeout=TIMEOUT)
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)
        node7ShardId = responseInJson['shard-id']
        self.assertEqual(node7ShardId, shard2)

        # get the members of shard2 from node4
        response = requests.get( 'http://localhost:8086/key-value-store-shard/shard-id-members/' + str(shard2), timeout=TIMEOUT)
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(node7SocketAddress in responseInJson['shard-id-members'])

        # get shard2 key count from node7
        response = requests.get( 'http://localhost:8089/key-value-store-shard/shard-id-key-count/' + str(shard2), timeout=TIMEOUT)
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)
        shard2KeyCountFromNode7 = int(responseInJson['shard-id-key-count'])

        # get shard2 key count from node3
        response = requests.get( 'http://localhost:8084/key-value-store-shard/shard-id-key-count/' + str(shard2), timeout=TIMEOUT)
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)
        shard2KeyCountFromNode3 = int(responseInJson['shard-id-key-count'])

        self.assertEqual(shard2KeyCountFromNode7, shard2KeyCountFromNode3)

    def test_h_impossible_reshard(self):

        print("\n###################### Doing Impossible Resharding ######################\n")

        response = requests.put('http://localhost:8083/key-value-store-shard/reshard', json={'shard-count': 10}, timeout=TIMEOUT)
        self.assertEqual(response.status_code, 400)

    def test_i_possible_reshard(self):

        print("\n###################### Doing Resharding ######################\n")

        response = requests.put('http://localhost:8082/key-value-store-shard/reshard', json={'shard-count': 3}, timeout=TIMEOUT)
        self.assertEqual(response.status_code, 200)

        time.sleep(20)

        # get the new shard IDs from node1
        response = requests.get( 'http://localhost:8082/key-value-store-shard/shard-ids', timeout=TIMEOUT)
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)
        newShardIds = responseInJson['shard-ids']
        newShardIdList = newShardIds
        self.assertEqual(len(newShardIdList), 3)

        shard1 = newShardIdList[0]
        shard2 = newShardIdList[1]
        shard3 = newShardIdList[2]


        # get the members of shard1 from node2
        response = requests.get( 'http://localhost:8083/key-value-store-shard/shard-id-members/' + str(shard1), timeout=TIMEOUT)
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)
        shard1Members = responseInJson['shard-id-members']
        self.assertGreater(len(shard1Members), 1)

        # get the members of shard2 from node3
        response = requests.get( 'http://localhost:8084/key-value-store-shard/shard-id-members/' + str(shard2), timeout=TIMEOUT)
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)
        shard2Members = responseInJson['shard-id-members']
        self.assertGreater(len(shard2Members), 1)

        # get the members of shard2 from node4
        response = requests.get( 'http://localhost:8086/key-value-store-shard/shard-id-members/' + str(shard3), timeout=TIMEOUT)
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)
        shard3Members = responseInJson['shard-id-members']
        self.assertGreater(len(shard3Members), 1)

        self.assertEqual(len(shard1Members + shard2Members + shard3Members), len(nodeSocketAddressList) + 1)

        # get the shard id of node4
        response = requests.get( 'http://localhost:8086/key-value-store-shard/node-shard-id', timeout=TIMEOUT)
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)

        node4ShardId = responseInJson['shard-id']

        self.assertTrue(node4ShardId in newShardIdList)

        if node4ShardId == shard1:
            self.assertTrue(nodeSocketAddressList[3] in shard1Members)
        elif node4ShardId == shard2:
            self.assertTrue(nodeSocketAddressList[3] in shard2Members)
        else:
            self.assertTrue(nodeSocketAddressList[3] in shard3Members)

        # get the shard1 key count from node5
        response = requests.get('http://localhost:8087/key-value-store-shard/shard-id-key-count/' + str(shard1), timeout=TIMEOUT)
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)
        shard1KeyCount = int(responseInJson['shard-id-key-count'])

        # get the shard2 key count from node3
        response = requests.get('http://localhost:8084/key-value-store-shard/shard-id-key-count/' + str(shard2), timeout=TIMEOUT)
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)
        shard2KeyCount = int(responseInJson['shard-id-key-count'])

        # get the shard3 key count from node1
        response = requests.get('http://localhost:8082/key-value-store-shard/shard-id-key-count/' + str(shard3), timeout=TIMEOUT)
        responseInJson = response.json()
        self.assertEqual(response.status_code, 200)
        shard3KeyCount = int(responseInJson['shard-id-key-count'])

        # sum of key counts in shards == total keys
        self.assertEqual(self.keyCount, shard1KeyCount + shard2KeyCount + shard3KeyCount)

        # check whether keys distributed almost uniformly
        minKeyCount = int ((self.keyCount * 0.75) / 3)
        maxKeyCount = int ((self.keyCount * 1.25) / 3)

        # minKeyCount < shard1-key-count < maxKeyCount
        self.assertGreater(shard1KeyCount, minKeyCount)
        self.assertLess(shard1KeyCount, maxKeyCount)

        # minKeyCount < shard2-key-count < maxKeyCount
        self.assertGreater(shard2KeyCount, minKeyCount)
        self.assertLess(shard2KeyCount, maxKeyCount)

        # minKeyCount < shard3-key-count < maxKeyCount
        self.assertGreater(shard3KeyCount, minKeyCount)
        self.assertLess(shard3KeyCount, maxKeyCount)

        for counter in range(self.keyCount):

            nodeIndex = (counter + 1 ) % len(nodeIpList)

            # get the value of the key
            response = requests.get('http://localhost:' + nodeHostPortList[nodeIndex] + '/key-value-store/key' + str(counter), timeout=TIMEOUT)
            responseInJson = response.json()
            self.assertEqual(response.status_code, 200)
            value = responseInJson["value"]
            self.assertEqual(value, "value" + str(counter))

    @classmethod
    def tearDownClass(cls):
        for i in range(1, 8):
            print("Cleaning up", str(i), "...")
            stopAndRemoveInstance("node" + str(i))
        print("Cleaning up", subnetName, "...")
        removeSubnet(subnetName)
        print("Done cleaning up.")

if __name__ == '__main__':
    unittest.main()
