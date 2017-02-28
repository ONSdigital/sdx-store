# sdx-store

[![Build Status](https://travis-ci.org/ONSdigital/sdx-store.svg?branch=master)](https://travis-ci.org/ONSdigital/sdx-store)

Scalable service for storing SDX data (backed by PostgreSQL).

## Prerequisites

A running instance of PostgreSQL. The service connects to `localhost` by default.

To override this export a set of `DB_XXXX` environment variables.

## Installation

Using virtualenv and pip, create a new environment and install within using:

    $ pip install -r requirements.txt

It's also possible to install within a container using docker. From the sdx-sequence directory:

    $ docker build -t sdx-store .

## Usage

Start the sdx-store service using the following command:

    python server.py

## API

There are four endpoints:
 * `GET /healthcheck` - returns a json response with key/value pairs describing the service state
 * `POST /responses` - store a json survey response
 * `GET /responses` - retrieve all survey responses
 * `GET /responses/<tx_id>` - retrieve a survey by transaction id

### Query parameters

The query parameters for `GET /responses` match the identifying data in the Json:
 * `survey_id`
 * `form`
 * `ru_ref`
 * `period`
 * `added_ms` - see below.

 These parameters do not all need to be provided, so you can choose how to select the survey responses you would like to receive.
