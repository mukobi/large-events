"""Unit tests for events service HTTP routes."""

# Copyright 2019 The Knative Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from unittest.mock import patch, MagicMock
import datetime
from contextlib import contextmanager
from bson import json_util
import mongomock
import app

EXAMPLE_TIME_STRING = datetime.datetime(
    2019, 6, 11, 10, 33, 1, 100000).isoformat(sep=' ', timespec='seconds')

VALID_REQUEST_INFO = {
    'event_name': 'valid_event',
    'description': 'This event is formatted correctly!',
    'author_id': 'admin',
    'event_time': EXAMPLE_TIME_STRING}
INVALID_REQUEST_INFO_MISSING_ATTRIBUTE = {
    'event_name': 'invalid_event_missing',
    'description': 'This event is missing an author!',
    'event_time': EXAMPLE_TIME_STRING}

VALID_EVENT_NAME = 'valid_event'
VALID_DB_EVENT = {
    'name': VALID_EVENT_NAME,
    'description': 'This event is formatted correctly!',
    'author': 'admin',
    'event_time': EXAMPLE_TIME_STRING,
    'created_at': EXAMPLE_TIME_STRING,
    'event_id': 'unique_event_id0'}
VALID_DB_EVENT_WITH_ID = {
    'name': 'different_event_name',
    'description': 'This event is formatted correctly too!',
    'author': 'admin',
    'event_time': EXAMPLE_TIME_STRING,
    'created_at': EXAMPLE_TIME_STRING,
    'event_id': 'unique_event_id1'}


@contextmanager
def environ(env):
    """Temporarily set environment variables inside the context manager and
    fully restore previous environment afterwards
    """
    original_env = {key: app.os.getenv(key) for key in env}
    app.os.environ.update(env)
    try:
        yield
    finally:
        for key, value in original_env.items():
            if value is None:
                del app.os.environ[key]
            else:
                app.os.environ[key] = value


class TestUploadEventRoute(unittest.TestCase):
    """Test add events endpoint POST /v1/add."""

    def setUp(self):
        """Set up test client and mock DB."""
        self.coll = mongomock.MongoClient().db.collection
        app.app.config['COLLECTION'] = self.coll
        app.app.config['TESTING'] = True
        self.client = app.app.test_client()

    def test_add_valid_event(self):
        """Test posting of valid event."""
        response = self.client.post('/v1/add', data=VALID_REQUEST_INFO)
        self.assertEqual(response.status_code, 201)

        self.assertEqual(self.coll.count_documents({}), 1)

    def test_add_invalid_event(self):
        """Test posting of invalid event with missing attributes."""
        response = self.client.post(
            '/v1/add', data=INVALID_REQUEST_INFO_MISSING_ATTRIBUTE)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(self.coll.count_documents({}), 0)

    def test_db_not_defined(self):
        """Test adding event when DB connection is undefined."""
        with environ(app.os.environ):
            if 'MONGODB_URI' in app.os.environ:
                del app.os.environ['MONGODB_URI']
            app.app.config['COLLECTION'] = app.connect_to_mongodb()
            response = self.client.post('/v1/add', data=VALID_REQUEST_INFO)
            self.assertEqual(response.status_code, 500)

            self.assertEqual(self.coll.count_documents({}), 0)


class TestGetEventsRoute(unittest.TestCase):
    """Test retrieve all events endpoint GET /v1/."""

    def setUp(self):
        """Set up test client and mock DB."""
        self.coll = mongomock.MongoClient().db.collection
        app.app.config['COLLECTION'] = self.coll
        app.app.config['TESTING'] = True
        self.client = app.app.test_client()
        self.fake_events = [
            VALID_DB_EVENT,
            VALID_DB_EVENT_WITH_ID
        ]

    def test_get_existing_events(self):
        """Test retrieving all events when valid events are added to the DB."""
        app.app.config['COLLECTION'].insert_many(self.fake_events)

        response = self.client.get('/v1/')
        self.assertEqual(response.status_code, 200)
        data = json_util.loads(response.data)

        self.assertEqual(len(data['events']), len(self.fake_events))
        self.assertEqual(data['num_events'], len(self.fake_events))

    def test_get_no_events(self):
        """Test retrieving all events when no events are in the DB."""
        response = self.client.get('/v1/')
        self.assertEqual(response.status_code, 200)
        data = json_util.loads(response.data)

        self.assertEqual(len(data['events']), 0)
        self.assertEqual(data['num_events'], 0)

    def test_db_not_defined(self):
        """Test getting events when DB connection is undefined."""
        with environ(app.os.environ):
            if 'MONGODB_URI' in app.os.environ:
                del app.os.environ['MONGODB_URI']
            app.app.config['COLLECTION'] = app.connect_to_mongodb()
            response = self.client.get('/v1/')
            self.assertEqual(response.status_code, 500)


class TestSearchEventsRoute(unittest.TestCase):
    """Test searching for an event by name at endpoint GET /v1/."""

    def setUp(self):
        """Set up test client and seed mock DB."""
        self.coll = mongomock.MongoClient().db.collection
        app.app.config['COLLECTION'] = self.coll
        app.app.config['TESTING'] = True
        self.client = app.app.test_client()
        self.fake_events = [
            VALID_DB_EVENT,
            VALID_DB_EVENT_WITH_ID
        ]
        self.coll.insert_many(self.fake_events)

    @patch('app.text_search_event_name', MagicMock(return_value=[VALID_DB_EVENT]))
    def test_search_existing_event(self):
        """Search for an event that exists in the DB."""
        response = self.client.get('/v1/search?name=' + VALID_EVENT_NAME)
        self.assertEqual(response.status_code, 200)
        data = json_util.loads(response.data)

        self.assertEqual(data['events'][0]['name'], VALID_EVENT_NAME)
        self.assertEqual(len(data['events']), 1)
        self.assertEqual(data['num_events'], 1)

    @patch('app.text_search_event_name', MagicMock(return_value=[VALID_DB_EVENT]))
    def test_search_existing_event_uppercase(self):
        """Search for an event that exists with different capitalization.

        The event should be found because search is case-insensitive.
        """
        response = self.client.get(
            '/v1/search?name=' + VALID_EVENT_NAME.upper())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(VALID_EVENT_NAME.upper(),
                         app.text_search_event_name.call_args[0][1])
        data = json_util.loads(response.data)

        self.assertEqual(data['events'][0]['name'], VALID_EVENT_NAME)
        self.assertEqual(len(data['events']), 1)
        self.assertEqual(data['num_events'], 1)

    @patch('app.text_search_event_name', MagicMock(return_value=[]))
    def test_search_nonexisting_event(self):
        """Search for an event that doesn't exist in the DB."""
        response = self.client.get('/v1/search?name=' + 'nonexistent event')
        self.assertEqual(response.status_code, 200)
        data = json_util.loads(response.data)

        self.assertEqual(len(data['events']), 0)
        self.assertEqual(data['num_events'], 0)

    def test_search_malformatted_name(self):
        """Malformatted query when searching for events."""
        response = self.client.get('/v1/search?bad_arg=' + 'not allowed')
        self.assertEqual(response.status_code, 400)

    def test_db_not_defined(self):
        """Test getting events when DB connection is undefined."""
        with environ(app.os.environ):
            if 'MONGODB_URI' in app.os.environ:
                del app.os.environ['MONGODB_URI']
            app.app.config['COLLECTION'] = app.connect_to_mongodb()
            response = self.client.get('/v1/search?name=' + VALID_EVENT_NAME)
            self.assertEqual(response.status_code, 500)


class TestGetEventByID(unittest.TestCase):
    """Test searching for an event by name at endpoint GET /v1/."""

    def setUp(self):
        """Set up test client and seed mock DB."""
        self.coll = mongomock.MongoClient().db.collection
        app.app.config['COLLECTION'] = self.coll
        app.app.config['TESTING'] = True
        self.client = app.app.test_client()
        self.fake_events = [
            VALID_DB_EVENT,
            VALID_DB_EVENT_WITH_ID
        ]
        self.coll.insert_many(self.fake_events)

    def test_search_existing_event(self):
        """Search for an event that exists in the DB."""
        id_to_search = VALID_DB_EVENT['_id']
        response = self.client.put(f'/v1/{id_to_search}')
        self.assertEqual(response.status_code, 200)
        data = json_util.loads(response.data)

        self.assertEqual(data['events'][0]['_id'], id_to_search)
        self.assertEqual(len(data['events']), 1)
        self.assertEqual(data['num_events'], 1)

    def test_search_nonexisting_event(self):
        """Search for an event that doesn't exist in the DB."""
        nonexistent_event_id = '123456789123456789123456'
        response = self.client.put('/v1/' + nonexistent_event_id)
        self.assertEqual(response.status_code, 200)
        data = json_util.loads(response.data)

        self.assertEqual(len(data['events']), 0)
        self.assertEqual(data['num_events'], 0)

    def test_db_not_defined(self):
        """Test getting events when DB connection is undefined."""
        id_to_search = VALID_DB_EVENT['_id']
        with environ(app.os.environ):
            if 'MONGODB_URI' in app.os.environ:
                del app.os.environ['MONGODB_URI']
            app.app.config['COLLECTION'] = app.connect_to_mongodb()
            response = self.client.put(f'/v1/{id_to_search}')
            self.assertEqual(response.status_code, 500)


if __name__ == '__main__':
    unittest.main()
