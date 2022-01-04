import mongoengine
from os import getenv

def global_init():
    data = {
        "username": getenv("MONGO_USER"),
        "password": getenv("MONGO_PASSWORD"),
        "host": getenv("MONGO_HOST"),
        "port": int(getenv("MONGO_PORT")),
        "authentication_source": getenv("MONGO_AUTH_SOURCE"),
        "authentication_mechanism": getenv("MONGO_AUTH_MECHANISM")
    }
    
    mongoengine.register_connection(alias='core', name='snake_bnb', **data)
