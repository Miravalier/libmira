#!/usr/bin/env python3.7

import boto3
import pyodbc
from contextlib import contextmanager

# Static globals
coh_instance_id = 'i-04c45a6b80fde0c27'
coh_group_id = 'sg-07e733a9cb561622f'
elastic_ip = '18.216.175.192'
any_ip = '0.0.0.0/0'
sql_driver = '{ODBC Driver 17 for SQL Server}'
sql_server = elastic_ip
sql_database = 'cohauth'

# Dynamic globals
_client = boto3.client('ec2')

with open("/etc/auth/coh.json") as fp:
    coh_credentials = json.load(fp)
    sql_username = coh_credentials['sql_username']
    sql_password = coh_credentials['sql_password']

sql_connection_string = "DRIVER={};SERVER={};DATABASE={};UID={};PWD={}".format(
    sql_driver, sql_server, sql_database, sql_username, sql_password
)


# AWS functions
def is_coh_running():
    """
    Returns true if the city of heroes server is running, false if the
    server is in any other state.
    """
    try:
        return _client.describe_instance_status(
            InstanceIds=[coh_instance_id]
        )['InstanceStatuses'][0]['InstanceState']['Name'] == 'running'
    except:
        return False


def start_coh():
    """
    Starts the city of heroes server.
    """
    _client.start_instances(InstanceIds=[coh_instance_id])


def stop_coh():
    """
    Stops the city of heroes server.
    """
    _client.stop_instances(InstanceIds=[coh_instance_id])


def open_coh_ports():
    """
    Adds the city of heroes connection ports to the city of heroes
    server access control list.
    """
    _client.authorize_security_group_ingress(
        CidrIp=any_ip,
        GroupId=coh_group_id,
        IpProtocol='tcp',
        FromPort=11228, # Start of port range
        ToPort=11228 # End of port range
    )
    _client.authorize_security_group_ingress(
        CidrIp=any_ip,
        GroupId=coh_group_id,
        IpProtocol='udp',
        FromPort=18000, # Start of port range
        ToPort=19000 # End of port range
    )


def close_coh_ports():
    """
    Removes the city of heroes connection ports from the city of heroes
    server access control list.
    """
    _client.revoke_security_group_ingress(
        CidrIp=any_ip,
        GroupId=coh_group_id,
        IpProtocol='tcp',
        FromPort=11228, # Start of port range
        ToPort=11228 # End of port range
    )
    _client.revoke_security_group_ingress(
        CidrIp=any_ip,
        GroupId=coh_group_id,
        IpProtocol='udp',
        FromPort=18000, # Start of port range
        ToPort=19000 # End of port range
    )


@contextmanager
def cursor():
    # Acquire resources
    connection = pyodbc.connect(sql_connection_string)
    _cursor = connection.cursor()
    try:
        yield _cursor
    finally:
        # Release resources
        _cursor.close()
        connection.close()


def players_connected():
    """
    Returns the number of currently active players on the city of heroes server.
    """
    connected_players = 0

    # Acquire cursor
    with cursor() as _cursor:
        _cursor.execute('''
            SELECT AuthName, Name
            FROM Cohdb.dbo.Ents
            WHERE Active > 0;
        ''')
        for entry in _cursor.fetchall():
            connected_players += 1

    # Return the number of connected players
    return connected_players
