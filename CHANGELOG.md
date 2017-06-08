### Unreleased
  - Timestamp all logs as UTC
  - Add common library logging configurator
  - Support UPDATE statements for duplicated tx_ids
  - Use Postgres backend via SQLAlchemy ORM.
  - Persist QueuePublishers
  - Add environment variables to README
  - Remove environment variable defaults
  - Correct license attribution
  - Add codacy badge

### 1.4.1 2017-03-15
  - Log version number on startup

### 1.4.0 2017-02-17
  - Add new `/invalid-responses` endpoint for viewing invalid submissions
  - Add change log
  - Add transaction ID (`tx_id`) to logging
  - Add logging of save action
  - Update python library '_requests_': `2.10.0` -> `2.12.4`
  - Hotfix for default queue names
  - Add support for new downstream CORA queue
  - Add queue name to log message

### 1.3.1 2016-12-13
  - Fix #18 incorrect queue names

### 1.3.0 2016-12-13
  - Add support for new downstream RRM and CTP queues

### 1.2.0 2016-11-28
  - Add storing of invalid submissions
  - Remove logging of failed submission data

### 1.1.1 2016-11-10
  - Remove logging of sensitive data

### 1.1.0 2016-09-19
  - Add configurable log level

### 1.0.0 2016-08-01
  - Initial release
