from hashlib import sha1
import hmac
import time

from . import settings

def create_url(path, method):
    expiry_time = int(time.time() + int(settings.CONFIG['SWIFT_DURATION']))
    path = '/v1/' + settings.CONFIG['SWIFT_BUCKET'] + '/' + path
    if method == 'GET':
        hmac_body = '%s\n%s\n%s' % ('GET', expiry_time, path)
    elif method == 'PUT':
        hmac_body = '%s\n%s\n%s' % ('PUT', expiry_time, path)
    sig = hmac.new(settings.CONFIG['SWIFT_KEY'].encode('utf-8'), hmac_body.encode('utf-8'), sha1).hexdigest()
    return '%s%s?temp_url_sig=%s&temp_url_expires=%d' % (settings.CONFIG['SWIFT_URL'], path, sig, expiry_time)
