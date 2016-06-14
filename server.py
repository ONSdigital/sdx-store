import settings
import json
import html
import logging
import logging.handlers
import requests
from flask import Flask, request, Response, jsonify, abort
from pymongo import MongoClient
import pymongo.errors
from datetime import datetime
from voluptuous import Schema, Coerce, All, Range, MultipleInvalid

app = Flask(__name__)

app.config['MONGODB_URL'] = settings.MONGODB_URL

mongo_client = MongoClient(app.config['MONGODB_URL'])
db = mongo_client.sdx_store

@app.route('/responses', methods=['POST'])
def do_save_response():
    survey_response = request.get_json(force=True)
    doc = {}
    doc['survey_response'] = survey_response
    doc['added_at'] = datetime.now()
    try:
        result = db.responses.insert_one( doc )
    except pymongo.errors.OperationFailure as e:
        return jsonify(error=str(e)), 400

    return jsonify(result="ok")

schema = Schema({
   'survey_id': str,
   'form': str,
   'ru_ref': str,
   'period': str,
   'per_page': All(Coerce(int), Range(min=1, max=100)),
   'page': All(Coerce(int), Range(min=1)),
})

@app.route('/responses', methods=['GET'])
def do_get_responses():
    try:
        schema(request.args)
    except MultipleInvalid as e:
        return jsonify(error=str(e)), 400
    survey_id = request.args.get('survey_id')
    form      = request.args.get('form')
    ru_ref    = request.args.get('ru_ref')
    period    = request.args.get('period')
    page      = request.args.get('page')
    per_page  = request.args.get('per_page')

    # paging defaults
    if not page:
        page = 1
    else:
        page = int(page)
    if not per_page:
        per_page = 100
    else:
        per_page = int(per_page)

    search_criteria = {}
    if survey_id: search_criteria['survey_response.survey_id'] = survey_id
    if form:      search_criteria['survey_response.form'] = form
    if ru_ref:    search_criteria['survey_response.metadata.ru_ref'] = ru_ref
    if period:    search_criteria['survey_response.collection.period'] = period

    results = {}
    responses  = []
    count = db.responses.count()
    results['count'] = count
    cursor = db.responses.find(search_criteria).skip(per_page*(page-1)).limit(per_page)
    for document in cursor:
        document['id'] = str(document['_id'])
        del document['_id']
        responses.append(document)
    results['responses'] = responses
    return jsonify(results)

if __name__ == '__main__':
    # Startup
    logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
    app.run(debug=True, host='0.0.0.0', port=5000)
