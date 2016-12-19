'''
Deduplicated remote events

Since many different actions can trigger a write of the target.json or rules
files, we need to handle some deduplication. This is handled by using the django
caching system to set a key and then triggering the actual event from middleware
'''

from django.contrib import messages

from promgen.signals import trigger_write_config, trigger_write_rules, trigger_write_urls


class RemoteTriggerMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        for (receiver, status) in trigger_write_config.send(self, force=True):
            if status:
                messages.info(request, 'Wrote Config')
        for (receiver, status) in trigger_write_rules.send(self, force=True):
            if status:
                messages.info(request, 'Wrote Rules')
        for (receiver, status) in trigger_write_urls.send(self, force=True):
            if status:
                messages.info(request, 'Wrote URLs')

        return response
