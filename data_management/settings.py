from django.conf import settings

CONFIG = {}
CONFIG['STORAGE_ROOT'] = getattr(settings, 'SCRC_STORAGE_ROOT')
CONFIG['SWIFT_URL'] = getattr(settings, 'SCRC_SWIFT_URL')
CONFIG['SWIFT_BUCKET'] = getattr(settings, 'SCRC_SWIFT_BUCKET')
CONFIG['SWIFT_KEY'] = getattr(settings, 'SCRC_SWIFT_KEY')
CONFIG['SWIFT_DURATION'] = getattr(settings, 'SCRC_SWIFT_DURATION')
