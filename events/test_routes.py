"""Unit tests for events service HTTP routes."""

import unittest
from unittest.mock import patch
import datetime
from bson import json_util
import mongomock
from app import app
from eventclass import Event

EXAMPLE_TIME = datetime.datetime(2019, 6, 11, 10, 33, 1, 100000)

VALID_REQUEST_INFO = {
    'event_name': 'valid_event',
    'description': 'This event is formatted correctly!',
    'author_id': 'admin',
    'event_time': EXAMPLE_TIME}
INVALID_REQUEST_INFO_MISSING_ATTRIBUTE = {
    'event_name': 'invalid_event_missing',
    'description': 'This event is missing an author!',
    'event_time': EXAMPLE_TIME}

VALID_DB_EVENT = {
    'name': 'valid_event',
    'description': 'This event is formatted correctly!',
    'author': 'admin',
    'event_time': EXAMPLE_TIME,
    'created_at': EXAMPLE_TIME,
    'event_id': 'unique_event_id0'}
VALID_DB_EVENT_WITH_ID = {
    'name': 'test_event',
    'description': 'This event is formatted correctly too!',
    'author': 'admin',
    'event_time': EXAMPLE_TIME,
    'created_at': EXAMPLE_TIME,
    'event_id': 'unique_event_id1'}


class TestUploadEventRoute(unittest.TestCase):
    """Test add events endpoint POST /v1/add."""
    def setUp(self):
        """Set up test client and mock DB."""
        self.coll = mongomock.MongoClient().db.collection
        app.config["COLLECTION"] = self.coll
        app.config["TESTING"] = True
        self.client = app.test_client()

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


class TestGetEventsRoute(unittest.TestCase):
    """Test retrieve all events endpoint GET /v1/."""
    def setUp(self):
        """Set up test client and mock DB."""
        self.coll = mongomock.MongoClient().db.collection
        app.config["COLLECTION"] = self.coll
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.FAKE_EVENTS = [
            VALID_DB_EVENT,
            VALID_DB_EVENT_WITH_ID
        ]

    def test_get_existing_events(self):
        """Test retrieving all events when valid events are added to the DB."""
        app.config["COLLECTION"].insert_many(self.FAKE_EVENTS)

        response = self.client.get('/v1/')
        self.assertEqual(response.status_code, 200)
        data = json_util.loads(response.data)

        self.assertEqual(len(data['events']), len(self.FAKE_EVENTS))
        self.assertEqual(data['num_events'], len(self.FAKE_EVENTS))

    def test_get_no_events(self):
        """Test retrieving all events when no events are in the DB."""
        response = self.client.get('/v1/')
        self.assertEqual(response.status_code, 200)
        data = json_util.loads(response.data)

        self.assertEqual(len(data['events']), 0)
        self.assertEqual(data['num_events'], 0)
