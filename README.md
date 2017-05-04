# sdx-store

[![Build Status](https://travis-ci.org/ONSdigital/sdx-store.svg?branch=master)](https://travis-ci.org/ONSdigital/sdx-store)

Scalable service for storing SDX data (backed by MongoDB).

## Prerequisites

A running instance of MongoDB. The service connects to `mongodb://localhost:27017` by default.

To override this export a `MONGODB_URL` environment variable.

## Installation

Using virtualenv and pip, create a new environment and install within using:

    $ pip install -r requirements.txt

It's also possible to install within a container using docker. From the sdx-sequence directory:

    $ docker build -t sdx-store .

## Usage

Start the sdx-store service using the following command:

    python server.py

## API

There are six endpoints:
 * `GET /invalid-responses` - returns a json response of all invalid responses in the connected database
 * `POST /queue` - Publishes a message to a corresponding rabbit message queue based on the message content. Returns a 200 response and JSON value `{"result": "ok"}` if the publish succeeds or a 500 response with JSON value `{"status": 500, "message": <error>}` if it does not.
 * `GET /healthcheck` - returns a json response with key/value pairs describing the service state
 * `POST /responses` - store a json survey response
 * `GET /responses` - retrieve a set of survey responses matching the query parameters
 * `GET /responses/<tx_id>` - retrieve a survey by id

## Configuration

Some of important environment variables available for configuration are listed below:

| Environment Variable    | Default                               | Description
|-------------------------|---------------------------------------|----------------
| MONGODB_URL             | `mongodb://localhost:27017`           | Location of MongoDB
| RABBIT_CS_QUEUE         | `sdx-cs-survey-notifications`         | Name of the Rabbit CS queue
| RABBIT_CTP_QUEUE        | `sdx-ctp-survey-notifications`        | Name of the Rabbit CTP queue
| RABBIT_CORA_QUEUE       | `sdx-cora-survey-notifications`       | Name of the Rabbit CORA queue
