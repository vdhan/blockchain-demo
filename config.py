import os


class Config(object):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SECRET_KEY = '?\xbf,\xb4\x8d\xa3"<\x9c\xb0@\x0f5\xab,w\xee\x8d$0\x13\x8b83'


class Dev(Config):
    HOST = '0.0.0.0'
    PORT = 10005
    DEBUG = True


class Product(Config):
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = False
