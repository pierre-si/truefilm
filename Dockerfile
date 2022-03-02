# syntax=docker/dockerfile:1

# use the official Python image that already has all the tools and packages
FROM python:3.9-slim-bullseye
# FROM postgres:13-buster
# SHELL ["/bin/bash", "-c"]
# instructs Docker to use this path as the default location for all subsequent commands
WORKDIR /app
# copy the requirements.txt file into our image.
COPY requirements.txt requirements.txt
#
RUN apt-get update && apt-get install -y wget postgresql
RUN pip3 install -r requirements.txt
# takes all the files located in the current directory and copies them into the image
COPY . .
# command we want to run when our image is executed inside a container
CMD ["sh", "extract.sh"]
