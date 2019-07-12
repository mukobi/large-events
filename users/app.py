"""
users/app.py
Authors: mukobi
Main flask app for users service
    - adding/updating users in the users db
    - getting the authorization level of a user


Copyright 2019 The Knative Authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
from flask import Flask, jsonify, request
import pymongo

app = Flask(__name__)  # pylint: disable=invalid-name

DB = None  # db initialized in main runtime


@app.route('/v1/authorization', methods=['POST'])
def get_authorization():
    """Finds whether the given user is authorized for edit access."""
    user = request.form.get('user_id')
    if user is None:
        return jsonify(error="You must supply a 'user_id' POST parameter!")
    authorized = find_authorization_in_db(user, DB.users_collection)
    return jsonify(edit_access=authorized)


@app.route('/v1/', methods=['PUT'])
def add_update_user():
    """Add or update the user in the db and returns new user object."""
    user = request.getJSON()
    if user is None:
        # TODO(mukobi) validate the user object has everything it needs
        return jsonify(error="You must supply a valid user in the body")
    # TODO(mukobi) add or update the user in the database
    added_new_user = True
    # TODO(mukobi) get the new user object from the db to return
    user_object = {
        "user_id": "0", "username": "Dummy User", "edit_access": False
    }
    return jsonify(user_object), (201 if added_new_user else 200)


def find_authorization_in_db(username, users_collection):
    """Queries the db to find authorization of the given user.

    Documents in the users collection should look like
        {"username": "cmei4444",
        "name": "Carolyn Mei",
        "is_organizer": True}
    """
    if users_collection.count_documents({"username": username}) == 0:
        return False  # user not found
    cursor = users_collection.find({"username": username})
    first_user = cursor[0]
    authorized = first_user.get("is_organizer")
    return False if authorized is None else authorized


@app.before_first_request
def initialize_mongodb():
    """Connect to MongoDB Atlas database using env vars.

    app.before_first_request decorator is used to keep
    the DB from initializing in testing to remove the
    dependency on the MongoDB connection in tests.
    """
    mongodb_atlas_username = os.environ.get(
        "MONGODB_ATLAS_USERNAME")
    mongodb_atlas_password = os.environ.get(
        "MONGODB_ATLAS_PASSWORD")
    mongodb_atlas_cluster_address = os.environ.get(
        "MONGODB_ATLAS_CLUSTER_ADDRESS")
    pymongo_uri = "mongodb+srv://{}:{}@{}".format(
        mongodb_atlas_username,
        mongodb_atlas_password,
        mongodb_atlas_cluster_address)
    DB = pymongo.MongoClient(pymongo_uri).users_db


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
