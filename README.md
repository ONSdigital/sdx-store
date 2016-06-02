[![Build Status](https://travis-ci.org/ONSdigital/sdx-store.svg?branch=master)](https://travis-ci.org/ONSdigital/sdx-store)

# sdx-store

Json store for SDX data.

## API

This component has a single API, `response`, which represents survey responses:
 * `POST` with Json in the body of the request to store a survey response.
 * `GET` with query parameters to retrieve a set of matching survey responses.

# Query parameers

The query parameters for `GET /response` match the identifying data in the Json:
 * `surveyId`
 * `formType`
 * `ruRef`
 * `period`
 * `addedMs` - see below.

These parameters do not all need to be provided, so you can choose how to select the
survey responses you would like to receive.

# Query response

The response to `GET /response` will contain a `totalHits` field, indicating the total number
of matched survey responses. This may be higher than the number returned, which is currently capped at 100.

The response also contains a field called `results`, which contains an array of result objects.

A result object consists of three fields:
 * `surveyResponse` contains the Json which was originally stored.
 * `addedDate` contains a readable date for when the survey response was added to the store.
 * `addedMs` contains a millisecond timestamp of the date for when the survey response was added to the store.

The `addedMs` value can be used in queries to filter to only return results on or after the given timestamp.
This is intended to be used for paging and batching of result.
