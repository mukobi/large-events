"""Main flask app for posts.
    - Serve stored media
    - Upload new posts to database
"""

# Authors: mukobi
# Copyright 2019 The Knative Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import pymongo
from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequestKeyError

app = Flask(__name__)  # pylint: disable=invalid-name


@app.route('/v1/add', methods=['POST'])
def upload_new_post():
    """Make a new post upload to the server.

    Post request body should contain:
    event_id: id of the event to post to
    author_id: user id of the user making the post
    text: text to be sent
    Post request files should contain all the files the user wants to upload
    to the server.
    """
    try:
        post = {
            "event_id": request.form["event_id"],
            "author_id": request.form["author_id"],
            "text":  request.form["text"],
            "files": [file for file in request.files.values()]
        }
        return str(upload_new_post_to_db(post, DB.posts_collection)), 201
    except BadRequestKeyError:
        return "Invalid request.", 400
    except ValueError:
        return "Post must contain text and/or files.", 400


@app.route('/v1/', methods=['GET'])
def get_all_posts():
    """Get all posts for the whole event."""


@app.route('/v1/<post_id>', methods=['GET'])
def get_post_by_id(post_id):
    """Get the post with the specified ID."""


@app.route('/v1/by_event/<event_id>', methods=['GET'])
def get_all_posts_for_event(event_id):
    """Get all posts matching the event with the specified ID."""


def upload_new_post_to_db(post, collection):
    """Uploads a new post to the db collection.

    Assumes the event matching the post's `event_id` and the user matching
        the post's `author_id` both exist. I.e. Caller should check this.

    Args:
        post (dict): Post to add. Requires exactly the following attributes:
            event_id (str): id of the event to post to
            author_id (str): user id of the user making the post
            text (str): text description
            files (list): list of string encoded files
        collection: pymongo collection to insert into.

    Returns:
        ObjectID: DB ID of the post that was uploaded.

    Raises:
        ValueError: Has no text body (i.e. empty string) nor any files
            to upload.
        AttributeError: `post` has not enough or too many attributes.
    """
    required_attributes = {"event_id", "author_id", "text", "files"}
    if post.keys() != required_attributes:
        raise AttributeError(f"Arg post must have exactly the "
                             "attributes {required_attributes}")
    if not post["text"] and not post["files"]:
        raise ValueError("One of text or files must not be empty.")
    # post is valid, add on timestamp and insert into db
    post["created_at"] = generate_timestamp()
    return collection.insert_one(post).inserted_id


def generate_timestamp() -> str:
    """Generate timestamp of the current time for placement in db.

    Returns:
        str: string representation of the current time.
    """
    # TODO use general timestamp generation function from events
    return "2017-10-06T00:00:00+00:00"


def connect_to_mongodb():  # pragma: no cover
    """Connect to MongoDB instance using env vars."""

    class DBNotConnectedError(EnvironmentError):
        """Raised when not able to connect to the db."""

    class Thrower():  # pylint: disable=too-few-public-methods
        """Used to raise an exception on failed db connect."""

        def __getattribute__(self, _):
            raise DBNotConnectedError(
                "Not able to find MONGODB_URI environment variable")

    mongodb_uri = os.environ.get("MONGODB_URI")
    if mongodb_uri is None:
        return Thrower()  # not able to find db config var
    return pymongo.MongoClient(mongodb_uri).posts_db


DB = connect_to_mongodb()  # None if can't connect


if __name__ == "__main__":  # pragma: no cover
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
