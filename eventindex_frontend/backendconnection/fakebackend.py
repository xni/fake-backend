from datetime import datetime, timedelta
import json
import os
import random
import sqlite3
import itertools


__author__ = 'stromsund@yandex-team.ru'
TIMESTAMP_FORMAT = '%Y%m%d%H%M%S'


def _get_connection():
    db_filename = os.path.join(os.path.dirname(__file__), 'hbase.mysql')
    c = sqlite3.connect(db_filename)

    cursor = c.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS queries ('
                   '    document_uuid TEXT,'
                   '    query         TEXT,'
                   '    timestamp     TEXT,'
                   '    PRIMARY KEY (document_uuid))')
    return c


def _get_search_result(query):
    checks = [p.split('=') for p in query.split()]
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'data.json')) as events_file:
        for line in events_file:
            event = json.loads(line)
            is_event_ok = True
            for param, value in checks:
                if str(event.get(param)) != value:
                    is_event_ok = False
                    break
            if is_event_ok:
                yield event


def find(document_uuid, query):
    connection = _get_connection()
    cursor = connection.cursor()
    query_time_seconds = random.randrange(5, 30)
    query_finish_timestamp = \
        (datetime.now() + timedelta(seconds=query_time_seconds))\
            .strftime(TIMESTAMP_FORMAT)
    cursor.execute(
        'INSERT INTO queries (document_uuid, query, timestamp)'
        'VALUES (?, ?, ?)',
        (document_uuid, query, query_finish_timestamp))
    connection.commit()
    connection.close()


def check_state(uuids):
    from __init__ import READY_STATUS, IN_PROGRESS_STATUS

    connection = _get_connection()
    cursor = connection.cursor()
    result = {}
    for uuid in uuids:
        cursor.execute(
            'SELECT timestamp FROM queries WHERE document_uuid = ?',
            (uuid, ))
        timestamp = datetime.strptime(cursor.fetchone()[0], TIMESTAMP_FORMAT)
        result[uuid] = (IN_PROGRESS_STATUS if datetime.now() < timestamp
                        else READY_STATUS)
    return result
    connection.close()


def get_search_result(uuid, limit, offset):
    connection = _get_connection()
    cursor = connection.cursor()
    cursor.execute('select query from queries where document_uuid = ?',
                   (uuid, ))
    query = cursor.fetchone()[0]
    return itertools.islice(_get_search_result(query), offset, offset + limit)


def download(results_uuid, search_document_uuid):
    find(results_uuid, search_document_uuid)
