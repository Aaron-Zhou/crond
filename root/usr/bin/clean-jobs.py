#!/usr/bin/env python2.7

from __future__ import print_function
import os
import sys
from datetime import datetime
from requests import get, delete
from dateutil.parser import parse

if len(sys.argv) not in [3, 4]:
    print('Usage: {} api-endpoint namespace [auth-token]'.format(sys.argv[0]))
    sys.exit(1)

api_endpoint = sys.argv[1] or os.environ.get('API_ENDPOINT')
assert api_endpoint, 'Missing parameter: api-endpoint'

namespace = sys.argv[2] or os.environ.get('NAMESPACE')
assert namespace, 'Missing parameter: namespace'

token = sys.argv[3] if len(sys.argv) > 3 else os.environ.get('TOKEN')
assert token, 'Missing parameter: auth-token'

ttl = int(os.environ['COMPLETION_LIMIT']) if 'COMPLETION_LIMIT' in os.environ else (60 * 60)

m, s = divmod(ttl, 60)
h, m = divmod(m, 60)

print('Searching for jobs older than {:02d}:{:02d}:{:02d}'.format(h, m, s))

headers = {
    'Authorization': 'Bearer {}'.format(token),
    'Content-type': 'application/yaml',
}

jobs_url = '{api}/apis/batch/v1/namespaces/{namespace}/jobs'.format(
    api=api_endpoint,
    namespace=namespace)

def url(obj):
    return '{}/{}'.format(api_endpoint, obj['metadata']['selfLink'])

def filter_valid_jobs(jobs):
    for job in jobs:
        metadata = job['metadata']
        try:
            created_by = metadata['annotations']['getup.io/created-by']
            status = job['status']
        except KeyError:
            continue

        completionTime = status.get('completionTime')
        if completionTime is None:
            continue

        now = datetime.utcnow()
        completionTime = parse(job['status']['completionTime'])
        now = now.replace(tzinfo=completionTime.tzinfo)

        elapsed = now - completionTime

        if elapsed.seconds > ttl:
            yield job

def list_pods_for_job(job):
    matchLabels = job['spec']['selector']['matchLabels']
    if matchLabels:
        url = '{api}/api/v1/namespaces/{namespace}/pods'.format(
            api=api_endpoint,
            namespace=namespace)
        labelSelector = ','.join([ '{}={}'.format(k,v) for k,v in matchLabels.items() ])
        res = get(url, params={'labelSelector': labelSelector}, headers=headers)
        if res.ok:
            data = res.json()
            for pod in data['items']:
                yield pod


def delete_job(job):
    print('Deleting job', job['metadata']['name'])
    for pod in list_pods_for_job(job):
        print('  -> Pod', pod['metadata']['selfLink'])
        delete(url(pod), headers=headers)
    print('  -> Job', job['metadata']['name'])
    delete(url(job), headers=headers)

res = get(jobs_url, headers=headers)
if not res.ok:
    print(res.status, res.reason)
    print(res.text)
    sys.exit(1)

data = res.json()
if not 'items' in data:
    print('Missing field: items')
    print(data)
    sys.exit(1)

jobs = data['items']
delete_list = sorted(
    filter_valid_jobs(jobs),
    key=lambda job: job['status']['completionTime']
)

if delete_list:
    print('Deleting {} of {} total jobs'.format(len(delete_list), len(jobs)))
else:
    print('No jobs to delete of {} total jobs'.format(len(jobs)))

map(delete_job, delete_list)
