from datetime import datetime, timedelta
import json
import os
from os import fdopen
import random
import sqlite3
import itertools


__author__ = 'stromsund@yandex-team.ru'
TIMESTAMP_FORMAT = '%Y%m%d%H%M%S'


def _get_connection():
    db_filename = os.path.join(os.path.dirname(__file__), 'hbase.mysql')
    connection = sqlite3.connect(db_filename)

    cursor = connection.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS queries ('
                   '    document_uuid TEXT,'
                   '    query         TEXT,'
                   '    timestamp     TEXT,'
                   '    PRIMARY KEY (document_uuid))')
    return connection


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
    from eventindex_frontend.backendconnection import READY_STATUS, \
        IN_PROGRESS_STATUS

    connection = _get_connection()
    cursor = connection.cursor()
    result = {}
    for cur_uuid in uuids:
        cursor.execute(
            'SELECT timestamp FROM queries WHERE document_uuid = ?',
            (cur_uuid, ))
        timestamp = datetime.strptime(cursor.fetchone()[0], TIMESTAMP_FORMAT)
        result[cur_uuid] = (IN_PROGRESS_STATUS if datetime.now() < timestamp
                            else READY_STATUS)
    connection.close()
    return result


def get_search_result(uuid, limit, offset):
    connection = _get_connection()
    cursor = connection.cursor()
    cursor.execute('select query from queries where document_uuid = ?',
                   (uuid, ))
    query = cursor.fetchone()[0]
    if limit is None:
        return itertools.islice(_get_search_result(query), offset, None)
    return itertools.islice(_get_search_result(query), offset, offset + limit)


def download(results_uuid, search_document_uuid):
    return find(results_uuid, search_document_uuid)


def check_download_state(download_task_ids):
    return check_state(download_task_ids)


def get_download_result(download_task_id, fd):
    connection = _get_connection()
    cursor = connection.cursor()
    cursor.execute('select query from queries where document_uuid = ?',
                   (download_task_id, ))
    search_task_id = cursor.fetchone()[0]
    data = "\n".join(json.dumps(event)
                     for event in get_search_result(search_task_id, None, 0))
    with fdopen(fd, 'w') as output_file:
        output_file.write(data)


def download_to_grid(search_task_uuid):
    return 'grid://' + search_task_uuid
