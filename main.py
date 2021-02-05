from itertools import groupby
from os import environ, fsync, rename, path
from json import dump
from time import sleep
import logging
import requests


__author__ = 'Taavi Väänänen'
__version__ = '0.1.0'
__license__ = 'BSD-3-Clause'


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(name)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%SZ'
)
logging.captureWarnings(True)
logger = logging.getLogger('puppy')
logger.setLevel(logging.DEBUG)


class Puppy:
    def __init__(self,
                 puppetdb_url: str,
                 puppetdb_resource: str):
        self.puppetdb_url = puppetdb_url
        self.puppetdb_resource = puppetdb_resource

        self.logger = logging.getLogger('puppy')

    def get_all(self):
        url = '{}/pdb/query/v4/resources/{}'.format(self.puppetdb_url, self.puppetdb_resource)
        self.logger.debug('Fetching data from %s', url)
        response = requests.get(url, headers={
            "User-Agent": 'puppy/{} (https://taavi.wtf/projects/puppy)'.format(__version__)
        })
        results = []

        for title, hosts in groupby(response.json(), lambda res: (res['title'])):
            results.append({
                "labels": {
                    "puppet_name": title
                },
                "targets": [
                    "{}:{}".format(host['parameters']['host'], host['parameters']['port']) for host in hosts
                ]
            })
        self.logger.debug('Got %s differently titled targets', len(results))

        return results


def getenv(name: str, default=None) -> str:
    if name not in environ:
        if default:
            return default

        raise Exception('No env values for {}'.format(name))
    return environ[name]


if __name__ == '__main__':
    puppy = Puppy(
        getenv('PUPPY_PUPPETDB_HOST'),
        getenv('PUPPY_PUPPETDB_RESOURCE')
    )

    delay = int(getenv('PUPPY_DELAY', 30))
    file = getenv('PUPPY_FILE')
    temp_file = '{}.new'.format(file)

    while True:
        data = puppy.get_all()

        with open(temp_file, 'w') as f:
            dump(data, f)
            f.flush()
            fsync(f.fileno())
        rename(temp_file, file)
        logger.info('Wrote %s. Waiting for %s seconds...', path.abspath(file), delay)

        sleep(delay)
