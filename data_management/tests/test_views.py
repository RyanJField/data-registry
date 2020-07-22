from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from data_management import models


class IndexViewTests(TestCase):

    @classmethod
    def _setup_database(cls):
        user = get_user_model()(username='Test User')
        user.save()
        st = models.StorageType(name='Test StorageType', updated_by=user)
        st.save()
        sr = models.StorageRoot(name='Test StorageRoot', updated_by=user, type=st)
        sr.save()
        sl = models.StorageLocation(name='Test StorageLocation', updated_by=user, store_root=sr, responsible_person=user)
        sl.save()
        i = models.Issue(name='Test Issue', data_object=sl, updated_by=user)
        i.save()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_database()

    def test_index_page_is_displayed(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_index_page_displays_each_data_object(self):
        response = self.client.get(reverse('index'))
        context = response.context[-1]
        objects = context['objects']
        object_names = sorted([o.name for o in objects])
        expected_names = sorted([n.lower() + 's' for n in models.all_object_models.keys()])
        self.assertEqual(object_names, expected_names)

    def test_index_page_displays_data_object_counts(self):
        response = self.client.get(reverse('index'))
        context = response.context[-1]
        objects = context['objects']
        sl_count = [o.count for o in objects if o.name == 'storagelocations'][0]
        self.assertEqual(sl_count, models.StorageLocation.objects.count())

    def test_index_page_displays_issues(self):
        response = self.client.get(reverse('index'))
        context = response.context[-1]
        issues = context['issues']
        expected_issues = models.Issue.objects.all()
        self.assertEqual(list(issues), list(expected_issues))
