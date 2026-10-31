"""Dependency-free Coulis clients. Source SDK: run from the repository root."""
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError


class CoulisError(Exception):
    def __init__(self, status, payload):
        self.status, self.payload = status, payload
        super().__init__(payload.get('error', {}).get('message', 'Coulis request failed'))


class WorkflowClient:
    def workflow(self, action, **arguments):
        return self.call('workflow', action=action, arguments=arguments)

    def context(self, text, surface='linkedin', **options):
        return self.call('context', text=text, surface=surface, **options)

    def check(self, text, surface='linkedin', **options):
        return self.call('check', text=text, surface=surface, **options)

    def critique(self, text, surface='linkedin', **options):
        return self.call('critique', text=text, surface=surface, **options)

    def learn(self, draft, final, surface='linkedin'):
        """Legacy edit capture; proposals do not activate preferences."""
        return self.call('learn', draft=draft, final=final, surface=surface)


class LocalClient(WorkflowClient):
    def __init__(self, profile_dir):
        self.profile_dir = profile_dir

    def call(self, operation, **arguments):
        from coulis_core.service import call
        return call(self.profile_dir, operation, arguments)


class Client(WorkflowClient):
    def __init__(self, base_url, api_key, profile_id='default', timeout=30):
        self.base_url, self.api_key = base_url.rstrip('/'), api_key
        self.profile_id, self.timeout = profile_id, timeout

    def call(self, operation, **arguments):
        if not operation.isidentifier():
            raise ValueError('Invalid operation')
        request = Request(self.base_url + '/v1/' + operation,
                          data=json.dumps({'profile_id': self.profile_id, 'arguments': arguments}).encode(),
                          headers={'Authorization': 'Bearer ' + self.api_key, 'Content-Type': 'application/json'})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.load(response)
        except HTTPError as error:
            with error:
                raise CoulisError(error.code, json.load(error)) from None
