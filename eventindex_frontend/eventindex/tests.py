import os
import time
from django.core.exceptions import ObjectDoesNotExist

from django.test import TestCase

import eventindex_frontend.backendconnection as backend

import models


class ModelsTest(TestCase):
    # http://djangosnippets.org/snippets/1029/
    fixtures = ["fake_users.json"]

    def test_search(self):
        search_task_id = models.SearchTask.start(
            "summary_hash|nBackTracks=3 summary_hash|nPV=1", 1)
        self.assertTrue(str(search_task_id).isdigit())

        result = None
        while result != backend.READY_STATUS:
            result = models.SearchTask.objects.get(pk=search_task_id).status()
            time.sleep(5)

        self.assertTrue(
            models.SearchTask.objects.get(pk=search_task_id).is_ready())

        limit = 5
        events = list(
            models.SearchTask.objects.get(pk=search_task_id).get(limit, 0))
        self.assertTrue(len(events) > 0)
        self.assertTrue(len(events) <= limit)

    def test_get_my_history(self):
        history = models.SearchTask.queries_by(1).order_by('query').all()
        self.assertTrue(len(history) == 0)
        models.SearchTask.start(
            "summary_hash|nBackTracks=3 summary_hash|nPV=1", 1)
        history = models.SearchTask.queries_by(1).order_by('query').all()
        self.assertTrue(len(history) == 1)

    def test_setting_favourite(self):
        models.SearchTask.start(
            "summary_hash|nBackTracks=3 summary_hash|nPV=1", 1)
        history = models.SearchTask.queries_by(1).order_by('query').all()
        history[0].is_favourite = True

    def test_download(self):
        self.test_search()
        history = models.SearchTask.queries_by(1).order_by('query').all()
        download_task_id = history[0].download()
        self.assertTrue(str(download_task_id).isdigit(), download_task_id)
        result = None
        while result != backend.READY_STATUS:
            result = \
                models.DownloadTask.objects.get(pk=download_task_id).status()
        result_path = models.DownloadTask.objects.get(pk=download_task_id)\
            .get_result()
        self.assertTrue(os.path.exists(result_path))
        os.remove(result_path)
        url = history[0].download_to_grid()
        self.assertTrue(len(url) > 0)
        code = history[0].get_downloader_script()
        self.assertTrue(len(code) > 0)

    def test_download_resume(self):
        self.test_search()
        history = models.SearchTask.queries_by(1).order_by('query').all()
        search_task = history[0]
        self.assertRaises(ObjectDoesNotExist,
                          getattr, search_task, 'downloadtask')
        download_task_id = search_task.download()
        self.assertEqual(download_task_id, search_task.download())
