CREATE TABLE IF NOT EXISTS responses (
  id    SERIAL PRIMARY KEY,
  added_date    timestamp WITH time zone,
  survey_response    jsonb
);