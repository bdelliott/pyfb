from django.conf import settings
from django.utils.importlib import import_module

class ConfigLoader(object):
    ''' Get configuration from Django settings.  Projects can supply a different impl to load config from an alternate source. '''
    
    def get(self, key):
        return eval("settings." + key)
    
# if a config loader implementation is specified in Django settings, use that.  otherwise defaults to getting configuration from Django settings directly

try:
    config_loader_module = import_module(settings.PYFB_CONFIG_LOADER)
    _loader = config_loader_module.ConfigLoader()
except AttributeError:
    _loader = ConfigLoader()

def get(key):
    return _loader.get(key)
    
    
    
    