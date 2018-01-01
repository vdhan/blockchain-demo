import argparse
import os

from flask import Flask

app = Flask(__name__)
conf = {
    'dev': 'config.Dev',
    'product': 'config.Product'
}

env = os.environ.get('ENV', 'dev')
app.config.from_object(conf[env])

if __name__ == '__main__':
    from view import *

    parser = argparse.ArgumentParser(description='Block chain demo')
    parser.add_argument('-V', '--version', action='version', version='1.0')
    parser.add_argument('-H', '--host', help='host', default=app.config['HOST'])
    parser.add_argument('-p', '--port', help='port', default=app.config['PORT'], type=int)
    args = parser.parse_args()
    app.run(args.host, args.port, app.config['DEBUG'])
