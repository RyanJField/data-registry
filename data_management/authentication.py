from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from rest_framework import authentication
from rest_framework import exceptions
import requests


class GitHubTokenAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        authorization = request.META.get('HTTP_AUTHORIZATION', b'')
        if not authorization:
            return None

        if len(authorization.split(' ')) == 2:
            token = authorization.split(' ')[1]
        else:
            raise exceptions.AuthenticationFailed('Token not supplied')

        headers = {'Authorization': 'token %s' % token}

        # Get username
        try:
            resp = requests.get('https://api.github.com/user', headers=headers)
            resp.raise_for_status()
            user_info = resp.json()
            username = user_info['login']
        except Exception:
            raise exceptions.AuthenticationFailed('Invalid token')

        # Check organization membership
        try:
            resp = requests.get('https://api.github.com/user/orgs', headers=headers)
            resp.raise_for_status()
            org_info = resp.json()
        except Exception:
            raise exceptions.AuthenticationFailed('Unable to obtain GitHub organizations')

        membership = False
        for org in org_info:
            if 'login' in org:
                if org['login'] == 'ScottishCovidResponse':
                    membership = True

        if not membership:
            raise exceptions.AuthenticationFailed('User not in required GitHub organization')

        try:
            user = get_user_model().objects.get(username=username)
        except Exception:
            raise exceptions.AuthenticationFailed('No such user')

        return user, None
