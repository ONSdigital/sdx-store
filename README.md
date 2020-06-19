# sdx-store

[![Build Status](https://travis-ci.org/ONSdigital/sdx-store.svg?branch=master)](https://travis-ci.org/ONSdigital/sdx-store) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/e482887a39f7445a8f960c8dda3c045a)](https://www.codacy.com/app/ons-sdc/sdx-store?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=ONSdigital/sdx-store&amp;utm_campaign=Badge_Grade) [![codecov](https://codecov.io/gh/ONSdigital/sdx-store/branch/master/graph/badge.svg)](https://codecov.io/gh/ONSdigital/sdx-store)

Scalable service for storing SDX data (backed by PostgreSQL).

## Prerequisites

A running instance of PostgreSQL.

## Installation
This application presently installs required packages from requirements files:
- `requirements.txt`: packages for the application, with hashes for all packages: see https://pypi.org/project/hashin/
- `test-requirements.txt`: packages for testing and linting

It's also best to use `pyenv` and `pyenv-virtualenv`, to build in a virtual environment with the currently recommended version of Python.  To install these, see:
- https://github.com/pyenv/pyenv
- https://github.com/pyenv/pyenv-virtualenv
- (Note that the homebrew version of `pyenv` is easiest to install, but can lag behind the latest release of Python.)

### Getting started
Once your virtual environment is set, install the requirements:
```shell
$ make build
```

To test, first run `make build` as above, then run:
```shell
$ make test
```

It's also possible to install within a container using docker. From the sdx-store directory:
```shell
$ docker build -t sdx-store .
```

## Usage

Start the sdx-store service using the following command:

```shell
$ python server.py
```
## API

There are six endpoints:
 * `GET /invalid-responses` - returns a json response of all invalid survey responses in the connected database
 * `POST /queue` - Publishes a message to a corresponding rabbit message queue based on the message content. Returns a 200 response and JSON value `{"result": "ok"}` if the publish succeeds or a 500 response with JSON value `{"status": 500, "message": <error>}` if it does not.
 * `GET /healthcheck` - returns a json response with key/value pairs describing the service state
 * `POST /responses` - store a json survey response
 * `GET /responses` - retrieve a JSON response of all valid survey responses in the connected responses.
 * `GET /responses/<tx_id>` - retrieve a survey by id
 * `DELETE /responses/old` - delete responses older than a number of days set in config 

### Query Parameters

The `/responses` and `/invalid-responses` endpoints support paging using URL query parameters.

* `per_page`: The number of responses to return per page. Must be in the range 1-100. Defaults to 1.
* `page`: The page number to return. Must be 1 or higher if set. Defaults to 1.

## Configuration

Some of important environment variables available for configuration are listed below:

| Environment Variable    | Example                               | Description
|-------------------------|---------------------------------------|----------------
| RABBIT_CS_QUEUE         | `sdx-cs-survey-notifications`         | Name of the Rabbit CS queue
| RABBIT_CTP_QUEUE        | `sdx-ctp-survey-notifications`        | Name of the Rabbit CTP queue
| RABBIT_CORA_QUEUE       | `sdx-cora-survey-notifications`       | Name of the Rabbit CORA queue
| RABBITMQ_HOST           | `rabbit`                              | Name of the Rabbit queue
| RABBITMQ_PORT           | `5672`                                | RabbitMQ port
| RABBITMQ_DEFAULT_USER   | `rabbit`                              | RabbitMQ username
| RABBITMQ_DEFAULT_PASS   | `rabbit`                              | RabbitMQ password
| RABBITMQ_DEFAULT_VHOST  | `%2f`                                 | RabbitMQ virtual host
| RABBITMQ_HOST2          | `rabbit`                              | RabbitMQ name
| RABBITMQ_PORT2          | `rabbit`                              | RabbitMQ port
| SDX_STORE_RESPONSE_RETENTION_DAYS |  `90`                       | Youngest response that will get deleted

### License

Copyright (c) 2016 Crown Copyright (Office for National Statistics)

Released under MIT license, see [LICENSE](LICENSE) for details.

