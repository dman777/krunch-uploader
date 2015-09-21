import os
import sys
import getpass
import json
import time
import logging
import pytz
from datetime import datetime
import threading
from dateutil import parser
import requests
logger = logging.getLogger('krunch')

class Authenticate(object):
    """Authenticates user using apikey"""

    def __init__(self, username, apikey):
        self.username = username
        self.apikey = apikey
        self.token = None
        self.expires = None
        self.jsonresp = None
        self._generate_token()
        self.lock = threading.Lock()

    url = 'https://identity.api.rackspacecloud.com/v2.0/tokens'
    utc = pytz.utc

    def _generate_token(self):
        msg = 'Initializing token....'
        logger.info(msg)
        try:
            jsonreq = {'auth': {'RAX-KSKEY:apiKeyCredentials': {'username': self.username,
                                                      'apiKey': self.apikey}}}
            auth_headers = {'content-type': 'application/json'}
            r = requests.post(self.url, data=json.dumps(jsonreq), headers=auth_headers)
            self.jsonresp = json.loads(r.text)
            self.token = str(self.jsonresp['access']['token']['id'])
            expires = str(self.jsonresp['access']['token']['expires'])
            msg = 'done!'
            logger.info(msg)
            self.expires = parser.parse(expires)
            msg = 'Nova token is: {}.\nToken expires is: {}'.format(self.token, self.expires.isoformat())
            logger.info(msg)
        except:
            msg = 'Bad name or apikey!'
            logger.error(msg)
            sys.exit()

    def get_token(self):
        with self.lock:
            current_time = datetime.now(self.utc).isoformat()
            current_time = parser.parse(current_time)
            if current_time < self.expires:
                return self.token
            self._generate_token()
            time.sleep(1)
            return self.token

