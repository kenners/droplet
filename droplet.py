#!/usr/bin/env python3
"""
droplet.py

A simple Digital Ocean CLI for creating, listing, and destroying droplets.
Uses the beta v2 of their API.

Expects an API key to be available as DIGITALOCEAN_API_KEY:
    $ export DIGITALOCEAN_API_KEY=yourapikeyhere
"""
import os
import sys
import argparse
import requests
try:
    import simplejson as json
except ImportError:
    import json

class Droplets():
    def __init__(self, cloud_conf_path=None):
        self.session = None
        self.api_url = "https://api.digitalocean.com/v2/droplets/"
        try:
            self.api_key = os.environ['DIGITALOCEAN_API_KEY']
        except KeyError:
            sys.exit('ERROR: You must set DIGITALOCEAN_API_KEY')
        self.headers = {"Content-Type": "application/json",
                        "Authorization": "Bearer {}".format(self.api_key)}
        self._create_session()
        try:
            self.cloud_conf = self._open_cloud_conf(cloud_conf_path)
        except TypeError:
            self.cloud_conf = None

    def _create_session(self):
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _open_cloud_conf(self, cloud_conf_path):
        try:
            with open(cloud_conf_path, 'r') as _:
                return _.read()
        except IOError as e:
            sys.exit('ERROR: Unable to open cloud_conf file\n {}'.format(e))

    @property
    def list(self):
        """Returns list of (ID, IP address) tuples of Droplets"""
        payload = {'page': 1, 'per_page': 1}
        try:
            req = self.session.get(self.api_url, params=payload)
        except requests.exceptions.ConnectionError as e:
            sys.exit('ERROR: Connection Error')
        req.raise_for_status()
        res = req.json(encoding='utf-8')
        return [(_['id'], _['networks']['v4'][0]['ip_address']) for _ in res['droplets']]

    def create(self, name='windsock', region='lon1', size='512mb', img='ubuntu-14-04-x64'):
        """Creates a Droplet"""
        cur = self.list
        # Only create new droplet if one doesn't always exist
        if not cur:
            payload = {
                        "name": name,
                        "region": region,
                        "size": size,
                        "image": img,
                        "ssh_keys": None,
                        "backups": False,
                        "ipv6": True,
                        "user_data": self.cloud_conf,
                        "private_networking": None
                        }
            try:
                req = self.session.post(self.api_url, json=payload)
            except requests.exceptions.ConnectionError as e:
                sys.exit('ERROR: Connection Error')
            req.raise_for_status()
            return None
        else:
            sys.exit('ERROR: A droplet already exists {}'.format(cur[0][0]))

    def destroy(self, vid=None):
        """Destroys a Droplet"""
        if vid is None:
            try:
                vid = self.list[0][0]
            except IndexError:
                sys.exit('No droplets to destroy.')
        try:
            req = self.session.delete(''.join([self.api_url, str(vid)]))
        except requests.exceptions.ConnectionError as e:
            sys.exit('ERROR: Connection Error')
        req.raise_for_status()

def main():
    parser = argparse.ArgumentParser(description="A simple Digital Ocean CLI for creating, listing, and destroying droplets.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter, epilog="Requires an API key to be supplied as the environmental variable $DIGITALOCEAN_API_KEY")
    parser.add_argument('action',
                        type=str,
                        nargs='?',
                        default='list',
                        help='list | create | destroy')
    parser.add_argument('cloud_conf_path',
                        type=str,
                        nargs='?',
                        help='cloud_config file')
    args = parser.parse_args()
    drop = Droplets(args.cloud_conf_path)
    if args.action in ("create", "c"):
        drop.create()
    elif args.action in ("destroy", "d"):
        drop.destroy()
    else:
        output = [('Droplet ID', 'IP Address')]
        output.extend(drop.list)
        for line in output:
            print("{0[0]:<25}{0[1]:<25}".format(line))
    parser.exit()

if __name__ == '__main__':
    main()
