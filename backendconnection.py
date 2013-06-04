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

    """
    new_document_uuid = str(uuid.uuid1())
    backend.find(new_document_uuid, query)
    return new_document_uuid


def check_state(uuids):
    """
    uuids: Iterable

    returns a dict[uuid] = state
    """
    return backend.check_state(uuids)


def get_search_result(uuid):
    """
    This result may be used for SERP-page and for Download.
    """
    assert check_state([uuid]).get(uuid, NOT_STARTED_STATUS) == READY_STATUS, \
        'Attempt to get result for unready search'
    return backend.get_search_result(uuid)