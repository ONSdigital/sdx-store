from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app import db


# pylint: disable=maybe-no-member
class SurveyResponse(db.Model):
    __tablename__ = 'responses'
    tx_id = db.Column("tx_id",
                      UUID,
                      primary_key=True)

    ts = db.Column("ts",
                   db.TIMESTAMP(timezone=True),
                   server_default=db.func.now(),
                   onupdate=db.func.now())

    invalid = db.Column("invalid",
                        db.Boolean,
                        default=False)

    data = db.Column("data", JSONB)

    def __init__(self, tx_id, invalid, data):
        self.tx_id = tx_id
        self.invalid = invalid
        self.data = data

    def __repr__(self):
        return '<SurveyResponse {}>'.format(self.tx_id)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class FeedbackResponse(db.Model):
    __tablename__ = "feedback_responses"
    id = db.Column("id",
                   Integer,
                   primary_key=True)

    ts = db.Column("ts",
                   db.TIMESTAMP(timezone=True),
                   server_default=db.func.now(),
                   onupdate=db.func.now())

    invalid = db.Column("invalid",
                        db.Boolean,
                        default=False)

    data = db.Column("data", JSONB)
    survey = db.Column("survey", String(length=25))
    period = db.Column("period", String(length=25))

    def __init__(self, invalid, data, survey, period):
        self.invalid = invalid
        self.data = data
        self.survey = survey
        self.period = period
