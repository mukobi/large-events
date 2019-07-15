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


def upsert_user_in_db(user_object, users_collection):
    """Updates or inserts the user object into user_collection.

    Adds the is_oganizer field to user_object with default False

    user_object should look like
        {"user_id": foobar,
         "name": Foo Bar}

    Documents in users_collection should look like
        {"user_id": foobar,
         "name": Foo Bar,
         "is_organizer": False}

    Returns:
        True if user_object was formatted correctly and the upsert
            was successful.
        False otherwise.
    """
    if "user_id" not in user_object or "name" not in user_object:
        # malformatted user_object
        return False
    # insert is_organizer field (default False)
    user_object["is_organizer"] = False
    # upsert user in db
    users_collection.update_one(
        {"user_id": user_object["user_id"]},
        {"set": {
            user_object
        }},
        upsert=True
    )
    return True


def find_authorization_in_db(username, users_collection):
    """Queries the db to find authorization of the given user.

    Documents in the users collection should look like
        {"user_id": foobar,
         "name": Foo Bar,
        "is_organizer": True}
    """
    first_user = users_collection.find_one({"user_id": username})
    if first_user is None:  # user not found
        return False
    authorized = first_user.get("is_organizer")
    return bool(authorized)  # handle 'None' case


def connect_to_mongodb():
    """Connect to MongoDB instance using env vars."""
    mongodb_uri = os.environ.get("MONGODB_URI")
    if mongodb_uri is None:
        print("Alert: not able to find MONGODB_URI environmental variable, "
              "no connection to MongoDB instance")
        return None  # not able to find db config var
    return pymongo.MongoClient(mongodb_uri).users_db


DB = connect_to_mongodb()  # None if can't connect


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
