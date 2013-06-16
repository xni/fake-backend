"""
This module is organized as a set of functions, because no state
is supposed. All session-wide objects are stored in the backend
layer.
"""

import tempfile
import uuid

import django.conf

import fakebackend as backend

__author__ = 'stromsund@yandex-team.ru'
READY_STATUS = 'ok'
NOT_STARTED_STATUS = 'not started'
IN_PROGRESS_STATUS = 'in progress'
DOWNLOAD_RESULT_IS_EXPIRED_STATUS = 'expired'


def find(query):
    """
    @returns: UUID of the document, where result will be stored.
    """
    new_document_uuid = str(uuid.uuid1())
    backend.find(new_document_uuid, query)
    return new_document_uuid


def check_state(uuids):
    """
    @type uuids: Iterable
    @rtype: dict[uuid] = state
    """
    return backend.check_state(uuids)


def get_search_result(search_task_id, limit=None, offset=None):
    """
    @param search_task_id: document_id of document with search results.
    @type search_task_id: basestring
    @returns: a list of events for selected op
    """
    assert check_state([search_task_id]).get(search_task_id,
                                             None) == READY_STATUS, \
        'Attempt to get result for unready search'
    return backend.get_search_result(search_task_id, limit, offset)


def download(search_task_uuid):
    """
    @returns: UUID of the document, where result will be stored.
    @rtype: basestring
    """
    new_document_uuid = str(uuid.uuid1())
    backend.download(new_document_uuid, search_task_uuid)
    return new_document_uuid


def check_download_state(uuids):
    """
    @param uuids: A list of download-task-ids to be checked.
    @type uuids: Iterable
    """
    return backend.check_download_state(uuids)


def get_download_result(download_task_id):
    """
    Downloads events from HBase to the local filesystem.

    @return: path to a file with events in the local filesystem.
    @rtype: basestring
    """
    assert check_download_state([download_task_id])\
        .get(download_task_id, None) == READY_STATUS, \
        'Attempt to get result for unready search'
    fd, path = tempfile.mkstemp(
        prefix='dwnl-ev-',
        dir=django.conf.settings.EVENT_DOWNLOAD_CACHE_PATH)
    backend.get_download_result(download_task_id, fd)
    return path


def download_to_grid(search_task_uuid):
    assert check_download_state([search_task_uuid])\
        .get(search_task_uuid, None) == READY_STATUS, \
        'Attempt to get result for unready search'
    return backend.download_to_grid(search_task_uuid)
