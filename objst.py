#
# objst.py - simple implementation of object store Web API
#
# Part of the material provided for assignment 1 of the Cloud
# Computing course at Leiden University.
#
# Copyright (C) 2019,2021,2022  Leiden University, The Netherlands
#


# Very simple Web API to implement simple object store functionality.
# Note that this code is not safe for concurrent access to the same
# data directory, it really only serves as simple test bed.
#
# Rate limiting can be configured at the bottom of this file.
# Random delays in serving requests can be configured just above
# the "random_delay" function definition.

from flask import Flask, request
from flask_restful import Resource, Api, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from pathlib import Path
import random
import time
import hashlib

app = Flask(__name__)
api = Api(app)

# Path to data directory where the objects will be stored. You might
# want to change this for your container deployment.
data_path = Path.cwd () / 'objects'

# global toggle for random delays
random_delay_enabled = True
random_delay_bounds = [5, 200]       # in milliseconds


#
# Random delay helper
#

def random_delay():
    if not random_delay_enabled:
        return

    time.sleep(random.randint(*random_delay_bounds) / 1000.)

#
# Simple data directory implementation
#

class DataDir:
    def __init__(self, datadir):
        if not datadir.exists():
            raise Exception("Specified data directory does not exist.")

        self.datadir = datadir

    def make_filename(self, obj_id):
        '''We simply use the object ID as filename for the object in
        the data directory.'''
        return self.datadir / obj_id

    def get_object(self, obj_id):
        filename = self.make_filename(obj_id)

        try:
            with filename.open("r") as fh:
                content = fh.read()
        except IOError:
            return None

        return content

    def exists(self, obj_id):
        return self.make_filename(obj_id).exists()

    def put_object(self, obj_id, content):
        filename = self.make_filename(obj_id)

        try:
            with filename.open("w") as fh:
                fh.write(content)
        except IOError:
            return False

        return True

    def delete_object(self, obj_id):
        filename = self.make_filename(obj_id)
        filename.unlink()

    def list_objects(self):
        return map(lambda f: str(f.name),
                   filter(lambda f: f.is_file(), self.datadir.iterdir()))

    def clear(self):
        for f in filter(lambda f: f.is_file(), self.datadir.iterdir()):
            f.unlink()


datadir = DataDir(data_path)


#
# API endpoints
#

class Object(Resource):
    def get(self, obj_id):
        random_delay()
        content = datadir.get_object(obj_id)
        if not content:
            abort(404)

        return content

    def put(self, obj_id):
        random_delay()
        success = datadir.put_object(obj_id, request.form['content'])
        if not success:
            abort(400)

        return obj_id, 200

    def delete(self, obj_id):
        random_delay()
        if not datadir.exists(obj_id):
            abort(404)

        datadir.delete_object(obj_id)
        return "", 200

class ObjectChecksum(Resource):
    def get(self, obj_id):
        content = datadir.get_object(obj_id)
        if not content:
            abort(404)

        m = hashlib.sha512()
        m.update(content.encode('ascii'))
        return m.hexdigest()

class ObjectStore(Resource):
    def get(self):
        random_delay()
        return list(map(str, datadir.list_objects()))

    def delete(self):
        random_delay()
        datadir.clear()
        return "", 200


api.add_resource(Object, '/objs/<string:obj_id>')
api.add_resource(ObjectChecksum, '/objs/<string:obj_id>/checksum')
api.add_resource(ObjectStore, '/')


#
# Configure rate limiting
#

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["10 per second"]
)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
