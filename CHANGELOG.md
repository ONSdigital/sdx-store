### Unreleased
  - Remove Cloudfoundry deployment files

### 3.13.0 2020-03-10
  - Add Vacancies to significant changes comment script (182-185).
  - Add MWSS to significant changes comment script (134)
  - Better handling of DataErrors that we get when null characters are in the submission

### 3.12.0 2020-01-30
  - Added comment script to return significant changes comments for E-commerce (187)

### 3.11.0 2020-01-27
  - Amend comment script to display respondent entered comments for MBS (009)

### 3.10.0 2019-12-18
  - Added delete old end point

### 3.9.4 2019-12-13
  - Amend comments script to handle '146a'

### 3.9.3 2019-11-08
  - Add python 3.8 to travis builds
  - Add url to logging metadata on an InvalidUsageError exception

### 3.9.2 2019-09-26
  - Update packages to bring them in line with other SDX repos

### 3.9.1 2019-05-31
  - Removed unused cryptography package

### 3.9.0 2019-05-31
  - Remove python 3.4 and 3.5 from travis builds
  - Update Jinja2 and urllib3 to fix security issue and test warnings
  - Update Flask, Flask-SQLAlchemy and other dependencies to fix security issues and test warnings

### 3.8.0 2019-02-08
  - Refactor code so that everything doesn't live in server.py

### 3.7.1 2018-12-20
  - Fix /invalid-responses endpoint
  - Validate tx_id is a real uuid in the /responses/<tx_id> endpoint

### 3.7.0 2018-12-12
  - Remove 'invalid' key from stored data
  - Add script that resets invalid stored data

### 3.6.0 2018-11-13
  - Add startup log with version

### 3.5.0 2018-10-22
  - Add MD5 hash to GET /responses

### 3.4.0 2018-08-13
  - Removed dependencies that were unused and had security vulnerabilities
  
### 3.3.0 2018-07-16
  - Add export comments script

### 3.2.0 2018-01-04
  - Add /info healthcheck endpoint

### 3.1.0 2017-11-21
  - Removed SDX common clone in docker
  - Begin using PyTest as default test runner
  - Add Cloudfoundry deployment files
  - Remove sdx-common logging

### 3.0.0 2017-09-11
  - Ensure integrity and version of library dependencies
  - Add transaction ID (`tx_id`) to message header
  - Remove queuing notifications

### 2.1.0 2017-07-25
  - Add support for feedback survey responses
  - Change all instances of ADD to COPY in Dockerfile
  - Remove use of SDX_HOME variable in makefile
  - Fix Postgres DB tests

### 2.0.0 2017-07-11
  - Version bump

### 1.5.0 2017-07-10
  - Timestamp all logs as UTC
  - Add common library logging configurator
  - Support UPDATE statements for duplicated tx_ids
  - Use Postgres backend via SQLAlchemy ORM.
  - Persist QueuePublishers
  - Add environment variables to README
  - Remove environment variable defaults
  - Correct license attribution
  - Add codacy badge
  - Add support for codecov to see unit test coverage
  - Update and pin version of sdx-common to 0.7.0
  - Add additional logging

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
