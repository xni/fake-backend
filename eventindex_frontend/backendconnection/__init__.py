"""
This module is organized as a set of functions, because no state
is supposed. All session-wide objects are stored in the backend
layer.
"""

import uuid

import fakebackend as backend

__author__ = 'stromsund@yandex-team.ru'
READY_STATUS = 'ok'
NOT_STARTED_STATUS = 'not started'
IN_PROGRESS_STATUS = 'in progress'


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


def get_search_result(uuid, limit=None, offset=None):
    assert check_state([uuid]).get(uuid, NOT_STARTED_STATUS) == READY_STATUS, \
        'Attempt to get result for unready search'
    return backend.get_search_result(uuid, limit, offset)


def download(query):
    """
    @returns: UUID of the document, where result will be stored.
    """
    new_document_uuid = str(uuid.uuid1())
    backend.download(new_document_uuid, query)
    return new_document_uuid
