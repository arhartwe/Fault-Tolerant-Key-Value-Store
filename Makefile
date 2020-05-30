IMG=assignment4-img
NETWORK=mynet

.PHONY: all init restart
all: destroy network build
init: network build 
restart: stop remove build2
allview: view1 view2 view3
allclock: getclock1 getclock2 getclock3

build: network
	docker build -t $(IMG) .
	
network:
	docker network create --subnet=10.10.0.0/16 $(NETWORK)

replica1:
	docker run --rm -p 8082:8085 --net=$(NETWORK) --ip=10.10.0.2 --name="node1" \
	-e SOCKET_ADDRESS="10.10.0.2:8085" -e VIEW="10.10.0.2:8085,10.10.0.3:8085,10.10.0.4:8085,10.10.0.5:8085,10.10.0.6:8085,10.10.0.7:8085" \
	-e SHARD_COUNT="2" $(IMG)

replica2:
	docker run --rm -p 8083:8085 --net=$(NETWORK) --ip=10.10.0.3 --name="node2" \
	-e SOCKET_ADDRESS="10.10.0.3:8085" -e VIEW="10.10.0.2:8085,10.10.0.3:8085,10.10.0.4:8085,10.10.0.5:8085,10.10.0.6:8085,10.10.0.7:8085" \
	-e SHARD_COUNT="2" $(IMG)

replica3:
	docker run --rm -p 8084:8085 --net=mynet --ip=10.10.0.4 --name="node3" \
	-e SOCKET_ADDRESS="10.10.0.4:8085" -e VIEW="10.10.0.2:8085,10.10.0.3:8085,10.10.0.4:8085,10.10.0.5:8085,10.10.0.6:8085,10.10.0.7:8085" \
	-e SHARD_COUNT="2" $(IMG)

replica4: 
	docker run --rm -p 8086:8085 --net=mynet --ip=10.10.0.5 --name="node4" \
        -e SOCKET_ADDRESS="10.10.0.5:8085" -e VIEW="10.10.0.2:8085,10.10.0.3:8085,10.10.0.4:8085,10.10.0.5:8085,10.10.0.6:8085,10.10.0.7:8085" \
        -e SHARD_COUNT="2" $(IMG)

replica5: 
	docker run --rm -p 8087:8085 --net=mynet --ip=10.10.0.6 --name="node5" \
        -e SOCKET_ADDRESS="10.10.0.6:8085" -e VIEW="10.10.0.2:8085,10.10.0.3:8085,10.10.0.4:8085,10.10.0.5:8085,10.10.0.6:8085,10.10.0.7:8085" \
        -e SHARD_COUNT="2" $(IMG)

replica6:
	docker run --rm -p 8088:8085 --net=mynet --ip=10.10.0.7 --name="node6" \
        -e SOCKET_ADDRESS="10.10.0.7:8085" -e VIEW="10.10.0.2:8085,10.10.0.3:8085,10.10.0.4:8085,10.10.0.5:8085,10.10.0.6:8085,10.10.0.7:8085" \
	-e SHARD_COUNT="2" $(IMG)

put1:
	curl --request PUT --header "Content-Type: application/json" --write-out "\n%{http_code}\n" --data '{"value":1, "causal-metadata": ""}' http://localhost:8082/key-value-store/x

put2:
	curl --request PUT --header "Content-Type: application/json" --write-out "\n%{http_code}\n" --data '{"value":1, "causal-metadata": ""}' http://localhost:8083/key-value-store/x

put3:
	curl --request PUT --header "Content-Type: application/json" --write-out "\n%{http_code}\n" --data '{"value":1, "causal-metadata": ""}' http://localhost:8084/key-value-store/x

update1: 
	curl --request PUT --header "Content-Type: application/json" --write-out "\n%{http_code}\n" --data '{"value":2, "causal-metadata": ""}' http://localhost:8083/key-value-store/x

update2:
	curl --request PUT --header "Content-Type: application/json" --write-out "\n%{http_code}\n" --data '{"value":10, "causal-metadata": ""}' http://localhost:8084/key-value-store/x

get1:
	curl --request GET --header "Content-Type: application/json" --write-out "\n%{http_code}\n" http://localhost:8082/key-value-store/x

get2:
	curl --request GET --header "Content-Type: application/json" --write-out "\n%{http_code}\n" http://localhost:8083/key-value-store/x

get3:
	curl --request GET --header "Content-Type: application/json" --write-out "\n%{http_code}\n" http://localhost:8084/key-value-store/x

view1:
	curl --request GET --header "Content-Type: application/json" --write-out "\n%{http_code}\n" http://localhost:8082/key-value-store-view

view2:
	curl --request GET --header "Content-Type: application/json" --write-out "\n%{http_code}\n" http://localhost:8083/key-value-store-view

view3:
	curl --request GET --header "Content-Type: application/json" --write-out "\n%{http_code}\n" http://localhost:8084/key-value-store-view

connect1:
	docker network connect mynet replica1

connect2:
	docker network connect mynet replica2

connect3:
	docker network connect mynet replica3

disconnect1:
	docker network disconnect mynet replica1

disconnect2:
	docker network disconnect mynet replica2

disconnect3:
	docker network disconnect mynet replica3

getclock1:
	curl --request GET --header "Content-Type: application/json" --write-out "\n%{http_code}\n" http://localhost:8082/get-local-clock

getclock2:
	curl --request GET --header "Content-Type: application/json" --write-out "\n%{http_code}\n" http://localhost:8083/get-local-clock

getclock3:
	curl --request GET --header "Content-Type: application/json" --write-out "\n%{http_code}\n" http://localhost:8084/get-local-clock

delete1:
	curl --request DELETE --header "Content-Type: application/json" --write-out "\n%{http_code}\n" --data '{"causal-metadata": ""}' http://localhost:8082/key-value-store/x

delete2:
	curl --request DELETE --header "Content-Type: application/json" --write-out "\n%{http_code}\n" --data '{"causal-metadata": ""}' http://localhost:8083/key-value-store/x

delete3:
	curl --request DELETE --header "Content-Type: application/json" --write-out "\n%{http_code}\n" --data '{"causal-metadata": ""}' http://localhost:8084/key-value-store/x

shardidmembers1:
	curl --request GET --header "Content-Type: application/json" --write-out "\n%{http_code}\n" http://localhost:8082/key-value-store-shard/shard-id-members/0

shardidmembers2:
	curl --request GET --header "Content-Type: application/json" --write-out "\n%{http_code}\n" http://localhost:8082/key-value-store-shard/shard-id-members/1


kill:
	docker kill $$(docker ps -q)
	
# This removes and kills ALL docker images on the system
# not just for this assignment.
destroy: # If failing you can try to run with the -i flag   
	docker kill $$(docker ps -q)
	docker rm $$(docker ps -a -q)
	docker rmi $$(docker images -q)
	docker network rm $(NETWORK)

# Stops all running containers and removes them
stop:
	docker stop $$(docker ps -a -q)

remove:
	docker container rm $$(docker container ls -aq)

stop_remove:
	docker stop $$(docker ps -a -q)
	docker container rm $$(docker container ls -aq)

build2: 
	docker build -t $(IMG) .

test:
	python3 test_assignment3.py