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

There are four endpoints:
 * `GET /healthcheck` - returns a json response with key/value pairs describing the service state
 * `POST /responses` - store a json survey response
 * `GET /responses` - retrieve a set of survey responses matching the query parameters
 * `GET /responses/<mongo_id>` - retrieve a survey by id

### Query parameters

The query parameters for `GET /responses` match the identifying data in the Json:
 * `survey_id`
 * `form`
 * `ru_ref`
 * `period`
 * `added_ms` - see below.

 These parameters do not all need to be provided, so you can choose how to select the survey responses you would like to receive.

### Query response

The response to `GET /responses` will contain a `total_hits` field, indicating the total number
of matched survey responses. This may be higher than the number returned, which is currently capped at 100.

The response also contains a field called `results`, which contains an array of result objects.

A result object consists of three fields:
 * `survey_response` contains the Json which was originally stored.
 * `added_date` contains a readable date for when the survey response was added to the store.
 * `added_ms` contains a millisecond timestamp of the date for when the survey response was added to the store.

The `added_ms` value can be used in queries to filter to only return results on or after the given timestamp.
This is intended to be used for paging and batching of result.
