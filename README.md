# sdx-store

[![Build Status](https://travis-ci.org/ONSdigital/sdx-store.svg?branch=master)](https://travis-ci.org/ONSdigital/sdx-store)

Scalable service for storing SDX data (backed by PostgreSQL).

## Prerequisites

A running instance of PostgreSQL.

## Installation

Using virtualenv, create a new environment, then install dependencies using:

    $ make build

It's also possible to install within a container using docker. From the sdx-store directory:

    $ docker build -t sdx-store .

## Usage

Start the sdx-store service using the following command:

    make start

## API

There are six endpoints:
 * `GET /invalid-responses` - returns a json response of all invalid survey responses in the connected database
 * `POST /queue` - Publishes a message to a corresponding rabbit message queue based on the message content. Returns a 200 response and JSON value `{"result": "ok"}` if the publish succeeds or a 500 response with JSON value `{"status": 500, "message": <error>}` if it does not.
 * `GET /healthcheck` - returns a json response with key/value pairs describing the service state
 * `POST /responses` - store a json survey response
 * `GET /responses` - retrieve a JSON response of all valid survey responses in the connected responses.
 * `GET /responses/<tx_id>` - retrieve a survey by id

### Query Parameters

The `/responses` and `/invalid-responses` endpoints support paging using URL query parameters.

* `per_page`: The number of responses to return per page. Must be in the range 1-100. Defaults to 1.
* `page`: The page number to return. Must be 1 or higher if set. Defaults to 1.

## Configuration

Some of important environment variables available for configuration are listed below:

| Environment Variable    | Default                               | Description
|-------------------------|---------------------------------------|----------------
| MONGODB_URL             | `mongodb://localhost:27017`           | Location of MongoDB
| RABBIT_CS_QUEUE         | `sdx-cs-survey-notifications`         | Name of the Rabbit CS queue
| RABBIT_CTP_QUEUE        | `sdx-ctp-survey-notifications`        | Name of the Rabbit CTP queue
| RABBIT_CORA_QUEUE       | `sdx-cora-survey-notifications`       | Name of the Rabbit CORA queue
