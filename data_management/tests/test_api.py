from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from .initdb import init_db


class UsersAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    # def _get_token(self):
    #     request = self.factory.get(reverse('get_token'))
    #     request.user = self.user
    #     response = views.get_token(request)
    #     self.assertEqual(response.status_code, 200)
    #     self.assert_(response.content.decode().startswith('Your token is: '))
    #     token = response.content.decode().replace('Your token is: ', '')
    #     return token

    def test_get_list_without_authentication(self):
        client = APIClient()
        url = reverse('user-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json(), {'detail': 'Authentication credentials were not provided.'})

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('user-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 4)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('user-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['username'], 'Test User')

    def test_filter_by_username(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('user-list')
        response = client.get(url, data={'username': 'testuserb'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['username'], 'testuserb')


class GroupsAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('group-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 0)


class StorageRootAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('storageroot-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 7)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('storageroot-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['root'], 'https://jptcp.com/')

    def test_filter_by_root(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('storageroot-list')
        response = client.get(url, data={'root': 'https://github.com'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['root'], 'https://github.com')

class StorageLocationAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('storagelocation-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 18)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('storagelocation-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['path'], 'master/SCRC/human/infection/SARS-CoV-2/symptom-probability/0.1.0.toml')

    def test_filter_by_path(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('storagelocation-list')
        response = client.get(url, data={'path': 'master/SCRC/human/infection/SARS-CoV-2/latent-period/0.1.0.toml'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['path'], 'master/SCRC/human/infection/SARS-CoV-2/latent-period/0.1.0.toml')

    def test_filter_by_hash(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('storagelocation-list')
        response = client.get(url, data={'hash': '43faf6d048b92ed1820db2e662ba403eb0e371fb'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['path'], 'human/infection/SARS-CoV-2/scotland/cases_and_management/v0.1.0.h5')


class ObjectAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('object-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 16)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('object-detail', kwargs={'pk': 3})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['storage_location'], 'http://testserver/api/storage_location/2/')

    def test_filter_by_storage_location(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('object-list')
        response = client.get(url, data={'storage_location': '3'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['storage_location'], 'http://testserver/api/storage_location/3/')


class ObjectComponentAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('objectcomponent-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 48)

    def test_get_detail_whole_object(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('objectcomponent-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['name'], 'whole_object')

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('objectcomponent-detail', kwargs={'pk': 17})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['name'], 'symptom-probability')

    def test_filter_by_name(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('objectcomponent-list')
        response = client.get(url, data={'name': 'nhs_health_board/per_location/all_deaths'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'nhs_health_board/per_location/all_deaths')


class IssueAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('issue-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 3)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('issue-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['description'], 'Test Issue 1')

    def test_filter_by_severity(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('issue-list')
        response = client.get(url, data={'severity': '6'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['description'], 'Test Issue 2')


class CodeRunAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('coderun-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('coderun-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['description'], 'Script run to upload and process scottish coronavirus-covid-19-management-information')

    def test_filter_by_run_date(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('coderun-list')
        response = client.get(url, data={'run_date': '2020-07-17T18:21:11Z'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['description'], 'Script run to upload and process scottish coronavirus-covid-19-management-information')

    def test_filter_by_description(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('coderun-list')
        response = client.get(url, data={'description': 'Script run to upload and process scottish coronavirus-covid-19-management-information'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['description'], 'Script run to upload and process scottish coronavirus-covid-19-management-information')

class ExternalObjectAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('externalobject-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 2)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('externalobject-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['other_unique_name'], 'scottish deaths-involving-coronavirus-covid-19')

    def test_filter_by_name(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('externalobject-list')
        response = client.get(url, data={'identifier': 'https://dx.doi.org/10.15586%2Fjptcp.v27iSP1.691'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['identifier'], 'https://dx.doi.org/10.15586%2Fjptcp.v27iSP1.691')

    def test_filter_by_title(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('externalobject-list')
        response = client.get(url, data={'title': 'scottish deaths-involving-coronavirus-covid-19'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['identifier'], 'https://dx.doi.org/10.15586%2Fjptcp.v27iSP1.691')


class QualityControlledAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('qualitycontrolled-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 3)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('qualitycontrolled-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['object'], 'http://testserver/api/object/15/')


class KeywordAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('keyword-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 5)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('keyword-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['keyphrase'], 'treatment')

    def test_filter_by_keyphrase(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('keyword-list')
        response = client.get(url, data={'keyphrase': 'monoclonal antibodies'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['keyphrase'], 'monoclonal antibodies')

    def test_filter_by_keyphrase_glob(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('keyword-list')
        response = client.get(url, data={'keyphrase': 'co*'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 2)


class AuthorAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('author-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 3)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('author-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['name'], 'Ivana Valenti')

    def test_filter_by_family_name(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('author-list')
        response = client.get(url, data={'name': '*ti'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 2)

    def test_filter_by_family_name_glob(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('author-list')
        response = client.get(url, data={'name': '*Cipriani'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Maria Cipriani')

    def test_filter_by_given_name(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('author-list')
        response = client.get(url, data={'name': 'Rosanna*'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Rosanna Massabeti')


class LicenceAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('licence-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('licence-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertIn('Copyright 2020 SCRC', response.json()['licence_info'])


class NamespaceAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('namespace-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 2)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('namespace-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['name'], 'FAIR')

    def test_filter_by_name(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('namespace-list')
        response = client.get(url, data={'name': 'simple_network_sim'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'simple_network_sim')

    def test_filter_by_name_glob(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('namespace-list')
        response = client.get(url, data={'name': '[fF]*'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)


class DataProductAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('dataproduct-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 13)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('dataproduct-detail', kwargs={'pk': 3})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['name'], 'human/infection/SARS-CoV-2/symptom-probability')

    def test_filter_by_namespace(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('dataproduct-list')
        response = client.get(url, data={'namespace': '1'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 9)

    def test_filter_by_name(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('dataproduct-list')
        response = client.get(url, data={'name': 'human/infection/SARS-CoV-2/latent-period'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'human/infection/SARS-CoV-2/latent-period')

    def test_filter_by_name_glob(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('dataproduct-list')
        response = client.get(url, data={'name': 'human/infection/SARS-CoV-2/*'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 7)

    def test_filter_by_version(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('dataproduct-list')
        response = client.get(url, data={'version': '0.1.0'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 13)


class CodeRepoReleaseAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('codereporelease-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('codereporelease-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['name'], 'ScottishCovidResponse/SCRCdata')

    def test_filter_by_name(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('codereporelease-list')
        response = client.get(url, data={'name': 'ScottishCovidResponse/SCRCdata'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'ScottishCovidResponse/SCRCdata')

    def test_filter_by_version(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('codereporelease-list')
        response = client.get(url, data={'version': '0.1.0'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'ScottishCovidResponse/SCRCdata')


class KeyvalueAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('keyvalue-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 4)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('keyvalue-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['key'], 'TestKey1')

    def test_filter_by_key(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('keyvalue-list')
        response = client.get(url, data={'key': 'TestKey2'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['key'], 'TestKey2')
