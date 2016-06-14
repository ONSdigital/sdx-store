# sdx-store

Json store for SDX data.

## API

This component has a single API, `responses`, which represents survey responses:
 * `POST` with Json in the body of the request to store a survey response.
 * `GET` with query parameters to retrieve a set of matching survey responses.

# Query parameters

The query parameters for `GET /responses` match the identifying data in the Json:
 * `survey_id`
 * `form`
 * `ru_ref`
 * `period`
 * `added_ms` - see below.

These parameters do not all need to be provided, so you can choose how to select the survey responses you would like to receive.

# Query response

The response to `GET /responses` will contain a `total_hits` field, indicating the total number
of matched survey responses. This may be higher than the number returned, which is currently capped at 100.

The response also contains a field called `results`, which contains an array of result objects.

A result object consists of three fields:
 * `survey_response` contains the Json which was originally stored.
 * `added_date` contains a readable date for when the survey response was added to the store.
 * `added_ms` contains a millisecond timestamp of the date for when the survey response was added to the store.

The `added_ms` value can be used in queries to filter to only return results on or after the given timestamp.
This is intended to be used for paging and batching of result.
