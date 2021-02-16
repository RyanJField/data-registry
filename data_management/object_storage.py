from configparser import ConfigParser
from hashlib import sha1
import hmac
import time

def create_url(path, method):
    config = ConfigParser()
    config.read('/home/ubuntu/config.ini')
    expiry_time = int(time.time()) + int(config['storage']['duration'])
    path = '/v1/' + config['storage']['bucket'] + '/' + path
    if method == 'GET':
        hmac_body = '%s\n%s\n%s' % ('GET', expiry_time, path)
    elif method == 'PUT':
        hmac_body = '%s\n%s\n%s' % ('PUT', expiry_time, path)
    sig = hmac.new(config['storage']['key'].encode('utf-8'), hmac_body.encode('utf-8'), sha1).hexdigest()
    return '%s%s?temp_url_sig=%s&temp_url_expires=%d' % (config['storage']['url'], path, sig, expiry_time)
