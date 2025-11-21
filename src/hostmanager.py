# coding=utf-8
"""
Updates hosts file based on docker containers
"""
import logging
import sys
from subprocess import check_output

__author__ = 'talpah@gmail.com'

import json
from os import getenv

import docker
from docker.errors import NotFound

from lib import Hosts

HOSTS_PATH = '/host_hosts'
DOMAIN_SUFFIX = '.local.development'

client = docker.from_env()
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def get_ip(container_id):
    """

    :param container_id:
    :return:
    """
    try:
        info = client.api.inspect_container(container_id)
    except NotFound:
        return None
    try:
        return info['NetworkSettings']['IPAddress']
    except KeyError:
        """/NetworkSettings/Networks/dressingbee_rbg/IPAddress"""
        for net in info['NetworkSettings']['Networks']:
            if info['NetworkSettings']['Networks'][net]['IPAddress']:
                return info['NetworkSettings']['Networks'][net]['IPAddress']


def get_hostname(container_id):
    """

    :param container_id:
    :return:
    """
    try:
        info = client.api.inspect_container(container_id)
    except docker.errors.NotFound:
        return None
    dom_name = DOMAIN_SUFFIX
    if info['Config']['Domainname']:
        dom_name = info['Config']['Domainname']
        if dom_name[0] != '.':
            dom_name = f".{dom_name}"
    if info['Config']['Hostname']:
        return f"{info['Config']['Hostname']}{dom_name}"
    else:
        return None


if __name__ == '__main__':
    # Reuse the global Docker client created above and avoid shadowing the
    # imported docker module. Shadowing would break references like
    # docker.errors.NotFound used in helper functions.
    hostname = getenv('HOSTNAME', None)
    if hostname:
        if '.' not in hostname:
            hostname = f"{hostname}{DOMAIN_SUFFIX}"
        logging.info(f"Adding {hostname}")
        hosts = Hosts(HOSTS_PATH)
        # logging.info(f"Existing hosts: {hosts.hosts}")
        my_ip = check_output(["/bin/sh", "-c", "ip -4 -f inet -o addr show eth0 | awk '{print $4}' | cut -d/ -f1"])
        my_ip = my_ip.decode().strip()
        logging.info(f'My IP: {my_ip}')
        hosts.set_one(hostname, my_ip)
        hosts.write(HOSTS_PATH)
        logging.info(f"Go to http://{hostname}/")
    """
    {
      "Type": "container",
      "Action": "start",
      "Actor": {
        "ID": "9c6478dd6b2e6c4be204155c505731ff81d0e04cfc1ba0ca0a5cf0ae3727acd4",
        "Attributes": {
          "com.docker.compose.config-hash": "fbbea28573d3694b76bf9df79a4011129dcddb62f17c3648cbf005d8c9391b76",
          "com.docker.compose.container-number": "1",
          "com.docker.compose.depends_on": "django:service_started:false",
          "com.docker.compose.image": "sha256:786ea2437356e5a233993d7b98b5dfa9e9bf71b30dd26a9a09d78ebb10346b55",
          "com.docker.compose.oneoff": "False",
          "com.docker.compose.project": "dressingbee",
          "com.docker.compose.project.config_files": "/home/cosmin/Projects/dressingbee/docker-compose.yml",
          "com.docker.compose.project.working_dir": "/home/cosmin/Projects/dressingbee",
          "com.docker.compose.replace": "celery-general-1",
          "com.docker.compose.service": "celery-general",
          "com.docker.compose.version": "2.40.3",
          "image": "dressingbee-local",
          "name": "dressingbee-celery-general-1"
        }
      },
      "scope": "local",
      "time": 1763722407,
      "timeNano": 1763722407082501844
    }
        
    """
    for event in client.events():
        # logging.info(f"Event received: {event}")
        event = json.loads(event)
        if 'Action' not in event:
            continue
        attributes = event.get('Actor', {}).get('Attributes', {})
        container_name = attributes.get('name', '')
        container_id = event.get("Actor", {}).get("ID", "")
        event_action = event['Action']

        if event_action in ['start', 'restart', 'unpause']:
            hostname = get_hostname(container_id)
            if hostname is None:
                logging.info(f"ERR: Event 'start' received but no hostname found for {container_name}. Skipping.")
                continue
            container_ip = get_ip(container_id)
            if not container_ip:
                logging.info(f"ERR: Could not find IP address for {hostname}. Skipping.")
                continue
            logging.info(f"Adding {hostname} as {container_ip}")
            hosts = Hosts(HOSTS_PATH)
            hosts.set_one(hostname, container_ip)
            hosts.write(HOSTS_PATH)
        elif event_action in ['die', 'stop', 'pause']:
            hostname = get_hostname(container_id)
            logging.info(f"Removing {hostname}")
            hosts = Hosts(HOSTS_PATH)
            hosts.remove_one(hostname)
            hosts.write(HOSTS_PATH)
