FROM python:3-slim
ADD server/ /server/
WORKDIR /server
RUN apt-get update
EXPOSE 8085
RUN pip3 install Flask requests
CMD python3 server.py
