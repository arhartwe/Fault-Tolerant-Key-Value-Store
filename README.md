# Fault Tolerant Key-Value Store

Python 3.7 implementation of an available, causally consistent, sharded, distributed key value store

## Docker Commands

### Subnet Creation

`docker network create --subnet=10.10.0.0/16 <SUBNET_NAME>`

### Image Build

`docker build -t <ASGN3_IMG> <PATH_TO_ASSIGNMENT>`

### Run Containers

`docker run --rm -p <EXPOSED_PORT>:8085 --net=<SUBNET_NAME> --ip=<IP_ADDRESS> --name=<REPLICA_NAME> -e SOCKET_ADDRESS=<SOCKET_ADDRESS> -e VIEW=<VIEWS> -e SHARD_COUNT=<SHARD_COUNT> <ASGN3_IMG>`

## Cleanup
If you would like to quickly stop all running containers:

`docker stop $(docker ps -a -q)`

If you would need to forcibly stop all containers:

`docker kill $$(docker ps -q)`

If you would like to quickly remove all containers (Note: this will remove ALL containers used and not used):

`docker container rm $(docker container ls -aq)`


## Citations

[Flask Quickstart](https://flask-restful.readthedocs.io/en/latest/quickstart.html)

[Flask + Docker](https://medium.com/@daniel.carlier/how-to-build-a-simple-flask-restful-api-with-docker-compose-2d849d738137)

[Flask + Docker Tutorial](https://medium.com/@doedotdev/docker-flask-a-simple-tutorial-bbcb2f4110b5)

[Flask API](https://blog.miguelgrinberg.com/post/designing-a-restful-api-using-flask-restful/page/6)
