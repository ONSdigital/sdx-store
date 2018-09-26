test_message = '''
{
  "type": "uk.gov.ons.edc.eq:surveyresponse",
  "origin": "uk.gov.ons.edc.eq",
  "survey_id": "194825",
  "version": "0.0.1",
  "tx_id": "ed7d29ed-612b-e981-d5ed-0e2e3c9951e3",
  "collection": {
    "exercise_sid": "hfjdskf",
    "instrument_id": "10",
    "period": "0616"
  },
  "submitted_at": "2016-03-12T10:39:40Z",
  "metadata": {
    "user_id": "789473423",
    "ru_ref": "1234570071A"
  },
  "data": {
    "1": "2",
    "2": "4",
    "3": "2",
    "4": "Y"
  }
}
'''

test_feedback_message = '''
 {
   "type" : "uk.gov.ons.edc.eq:feedback",
   "origin" : "uk.gov.ons.edc.eq",
   "metadata": {
    "user_id": "789473423",
    "ru_ref": "432423423423"
   },
   "data": {
    "url": "https://eq.onsdigital.uk/feedback",
    "name": "John Appleseed",
    "email": "john.appleseed@ons.gov.uk",
    "message": "Feedback message string"
   },
   "submitted_at": "2016-03-07T15:28:05Z",
   "collection": {
    "instrument_id": "0203",
    "exercise_sid": "739",
    "period": "2016-02-01"
   },
   "survey_id": "023",
   "tx_id": "0f534ffc-9442-414c-b39f-a756b4adc6cb",
   "version" : "0.0.1"
 }
 '''

invalid_feedback_message = '''
 {
   "invalid": true,
   "origin": "uk.gov.ons.edc.eq",
   "survey_id": "feedback",
   "associated_survey": "RSI",
   "submitted_at": "2016-03-12T10:39:40Z",
   "satisfaction": "satisfied",
   "comment": "comment",
   "collection": {
    "exercise_sid": "hfjdskf",
    "instrument_id": "1",
    "period": "0616"
    }

 }
 '''

second_test_message = '''
{
  "type": "uk.gov.ons.edc.eq:surveyresponse",
  "origin": "uk.gov.ons.edc.eq",
  "survey_id": "194826",
  "version": "0.0.1",
  "tx_id": "e7d45533-71a9-44fe-8077-621d1ab423cd",
  "collection": {
    "exercise_sid": "hfjdskf",
    "instrument_id": "10",
    "period": "0617"
  },
  "submitted_at": "2016-03-12T10:39:40Z",
  "metadata": {
    "user_id": "789473423",
    "ru_ref": "1234570081A"
  },
  "data": {
    "1": "2",
    "2": "4",
    "3": "2",
    "4": "Y"
  }
}
'''

missing_tx_id_message = '''
{
"type": "uk.gov.ons.edc.eq:surveyresponse",
  "origin": "uk.gov.ons.edc.eq",
  "survey_id": "194826",
  "version": "0.0.1",
  "collection": {
    "exercise_sid": "hfjdskf",
    "instrument_id": "10",
    "period": "0617"
  },
  "submitted_at": "2016-03-12T10:39:40Z",
  "metadata": {
    "user_id": "789473423",
    "ru_ref": "1234570081A"
  },
  "data": {
    "1": "2",
    "2": "4",
    "3": "2",
    "4": "Y"
  }
}
'''

invalid_message = '''
{
  "invalid": true,
  "type": "uk.gov.ons.edc.eq:surveyresponse",
  "origin": "uk.gov.ons.edc.eq",
  "survey_id": "194826",
  "version": "0.0.1",
  "tx_id": "ed7d29ed-612b-e981-d5ed-0e2e3c9951e3",
  "collection": {
    "exercise_sid": "hfjdskf",
    "instrument_id": "10",
    "period": "0617"
  },
  "submitted_at": "2016-03-12T10:39:40Z",
  "metadata": {
    "user_id": "789473423",
    "ru_ref": "1234570081A"
  },
  "data": {
    "1": "2",
    "2": "4",
    "3": "2",
    "4": "Y"
  }
}
'''
