import os

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

import eventindex_frontend.backendconnection as backend


class NotYourObjectException(Exception):
    """ This exception is raised, then the user tries to get or
        modify an object, that he does not own.
    """


class SearchTask(models.Model):
    user = models.ForeignKey(User)
    related_uuid = models.CharField(max_length=20, unique=True, blank=False,
                                    null=False)
    query = models.TextField(null=False, blank=False)
    is_favourite = models.BooleanField(default=False, null=False)
    started_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def start(query, user_id):
        """
        Start a search task.

        @param query: User's request.
        @type query: basestring
        @param user_id: Id of the user, who typed the query.
        @type user_id: int
        @return: Id of the created task.
        @rtype: int
        """
        new_task = SearchTask(user=User.objects.get(pk=user_id),
                              related_uuid=backend.find(query),
                              query=query,
                              is_favourite=False)
        new_task.save()
        return new_task.id

    @staticmethod
    def queries_by(user_id):
        """
        Helper for retrieving history of search queries for a particular user.

        @param user_id: id of a user, whose history is to be retrieved.
        @type user_id: int
        @returns: QuerySet with appropriate filters applied.
        @rtype: django.db.models.QuerySet
        """
        return SearchTask.objects.filter(user__id=user_id)

    def status(self):
        """
        Get task's status.

        @returns: eventindex_frontend.backendconnection.*_STATUS
        @rtype: basestring
        """
        return backend.check_state([self.related_uuid])[self.related_uuid]

    def is_ready(self):
        """
        @returns: if this search task is complete and results are available.
        @rtype: bool
        """
        return self.status() == backend.READY_STATUS

    def get(self, limit=None, offset=None):
        """
        Fetch search results.

        @param limit: output not more than limit events
        @type limit: int
        @param offset: output events starting from offset'th
        @type offset: int
        @returns: a list of events
        @rtype: list
        """
        return backend.get_search_result(self.related_uuid, limit, offset)

    def download(self):
        """
        Start downloading events for the current search result.

        @return: DownloadTask.id for the related download task.
        @rtype: int
        """
        assert self.is_ready()
        try:
            return self.downloadtask.id
        except ObjectDoesNotExist:
            DownloadTask.start(self)
        return self.downloadtask.id

    def download_to_grid(self):
        """
        @return: Link to grid task
        @rtype: basestring
        """
        assert self.is_ready()
        return backend.download_to_grid(self.related_uuid)

    def get_downloader_script(self):
        """
        @return: code for manual download events.
        @rtype: basestring
        """
        assert self.is_ready()
        return ScriptTemplate.get_downloader_script(self.related_uuid)


class DownloadTask(models.Model):
    search_task = models.OneToOneField(SearchTask, null=False, unique=True)
    related_uuid = models.CharField(max_length=20, unique=True, blank=False,
                                    null=False)
    results_path = models.CharField(max_length=400, null=True, unique=True)

    @staticmethod
    def start(search_task):
        assert search_task.is_ready()
        DownloadTask(
            search_task=search_task,
            related_uuid=backend.download(search_task.related_uuid)).save()

    def status(self):
        """
        @return: status of the current DownloadTask.
                 eventindex_frontend.backendconnection.*_STATUS
        @rtype: int
        """
        return backend\
            .check_download_state([self.related_uuid])[self.related_uuid]

    def get_result(self):
        """
        @return: path to a file with downloaded events.
        @rtype: unicode
        """
        assert self.status() in (backend.READY_STATUS,
                                 backend.DOWNLOAD_RESULT_IS_EXPIRED_STATUS), \
            'Attempt to get result for unready download'
        if self.results_path and os.path.exists(self.results_path):
            return self.results_path
        self.results_path = backend.get_download_result(self.related_uuid)
        self.save()
        return self.results_path


class ScriptTemplate(models.Model):
    name = models.CharField(max_length=40, unique=True, null=False,
                            blank=False)
    value = models.TextField(blank=False, null=False)

    @staticmethod
    def get_downloader_script(search_task_document_id):
        """
        @param search_task_document_id: id of a document with search results
        @type search_task_document_id: basestring
        @return: code for downloading found events.
        @rtype: basestring
        """
        all_events = backend.get_search_result(search_task_document_id,
                                               None, 0)
        return '''#!/bin/sh
wget events://{0}'''.format('+'.join(e.get('rawID', '') for e in all_events))
