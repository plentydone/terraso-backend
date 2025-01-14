# Copyright © 2021-2023 Technology Matters
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see https://www.gnu.org/licenses/.

import functools
import json
from typing import Optional
from urllib.parse import urlparse

import httpx
import structlog
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import login as dj_login
from django.contrib.auth import logout as dj_logout
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views import View

from .constants import OAUTH_COOKIE_MAX_AGE_SECONDS, OAUTH_COOKIE_NAME
from .providers import AppleProvider, GoogleProvider, MicrosoftProvider
from .services import (
    AccountService,
    JWTService,
    PlausibleService,
    TokenExchangeException,
    TokenExchangeService,
)

logger = structlog.get_logger(__name__)
User = get_user_model()
jwt_service = JWTService()


class AbstractAuthorizeView(View):
    def get(self, request, *args, **kwargs):
        state = request.GET.get("state")
        return JsonResponse({"request_url": self.provider.login_url(state=state)})

    @property
    def provider(self):
        return NotImplementedError("AbstractAuthorizeView must be inherited")


class GoogleAuthorizeView(AbstractAuthorizeView):
    @property
    def provider(self):
        return GoogleProvider


class AppleAuthorizeView(AbstractAuthorizeView):
    @property
    def provider(self):
        return AppleProvider


class MicrosoftAuthorizeView(AbstractAuthorizeView):
    @property
    def provider(self):
        return MicrosoftProvider


class AbstractCallbackView(View):
    def get(self, request, *args, **kwargs):
        self.authorization_code = self.request.GET.get("code")
        self.error = self.request.GET.get("error")
        self.state = self.request.GET.get("state", "")

        return self.process_callback(request)

    def post(self, request, *args, **kwargs):
        self.authorization_code = self.request.POST.get("code")
        self.error = self.request.POST.get("error")
        self.state = self.request.POST.get("state", "")

        return self.process_callback(request)

    @classmethod
    def _check_cookie(cls, cookie):
        """Double check to make sure the redirect URI makes sense"""
        try:
            url = urlparse(cookie)
            if url.hostname:
                return False
            return url.path.startswith(reverse("oauth2_provider:authorize"))
        except ValueError:
            return False

    def process_callback(self, req):
        if self.error:
            logger.error("Auth provider returned error on callback", extra={"error": self.error})
            return HttpResponse(f"Error: {self.error}", status=400)

        if not self.authorization_code:
            logger.error("No authorization code from auth provider on callback")
            return HttpResponse("Error: no authorization code informed", status=400)

        try:
            user, created_with_service = self.process_signup()
            access_token, refresh_token = terraso_login(self.request, user)
        except Exception as exc:
            logger.exception("Error attempting create access and refresh tokens")
            return HttpResponse(f"Error: {exc}", status=400)

        redirect_uri = f"{settings.WEB_CLIENT_URL}/{self.state}"
        if cookie := req.get_signed_cookie(
            OAUTH_COOKIE_NAME, None, max_age=OAUTH_COOKIE_MAX_AGE_SECONDS
        ):
            # we stored the original URI as a cookie
            # redirecting the user to this URI will start our OAuth process
            if self._check_cookie(cookie):
                redirect_uri = cookie
        response = HttpResponseRedirect(redirect_uri)
        response.delete_cookie("oauth")
        response.set_cookie("atoken", access_token, domain=settings.AUTH_COOKIE_DOMAIN)
        response.set_cookie("rtoken", refresh_token, domain=settings.AUTH_COOKIE_DOMAIN)
        if created_with_service:
            # Set samesite to avoid warnings
            plausible_service = PlausibleService()
            try:
                plausible_service.track_signup(created_with_service, self.request)
            except httpx.HTTPStatusError as e:
                logger.error(
                    "Error tracking signup: received status code %s when querying %s",
                    e.response.status_code,
                    e.request.url,
                )
            except Exception:
                logger.exception("Error tracking signup")

        return response

    def process_signup(self):
        raise NotImplementedError("AbstractCallbackView must be inherited.")


def record_creation(service):
    """A simple decorator to store if a new user has been created, and by which service"""

    def wrapper(f):
        @functools.wraps(f)
        def g(*args, **kwargs):
            user, created = f(*args, **kwargs)
            if created:
                return user, service
            else:
                return user, None

        return g

    return wrapper


class GoogleCallbackView(AbstractCallbackView):
    @record_creation("google")
    def process_signup(self):
        return AccountService().sign_up_with_google(self.authorization_code)


class AppleCallbackView(AbstractCallbackView):
    @record_creation("apple")
    def process_signup(self):
        user_obj = self.request.POST.get("user", "{}")
        try:
            apple_user_data = json.loads(user_obj)
        except json.JSONDecodeError:
            error_msg = "Couldn't parse User data from Apple"
            logger.error(error_msg, extra={"user_obj", user_obj})
            raise Exception(error_msg)

        first_name = apple_user_data.get("name", {}).get("firstName", "")
        last_name = apple_user_data.get("name", {}).get("lastName", "")

        return AccountService().sign_up_with_apple(
            self.authorization_code, first_name=first_name, last_name=last_name
        )


class MicrosoftCallbackView(AbstractCallbackView):
    @record_creation("microsoft")
    def process_signup(self):
        return AccountService().sign_up_with_microsoft(self.authorization_code)


class RefreshAccessTokenView(View):
    def post(self, request, *args, **kwargs):
        try:
            request_data = json.loads(request.body)
        except json.decoder.JSONDecodeError:
            logger.error("Failure parsing refresh token request body", extra={"body": request.body})
            return JsonResponse({"error": "The request expects a JSON body"}, status=400)

        try:
            refresh_token = request_data["refresh_token"]
        except KeyError:
            logger.error("Refresh token request without 'refresh_token' parameter")
            return JsonResponse(
                {"error": "The request expects a 'refresh_token' parameter"}, status=400
            )

        try:
            refresh_payload = jwt_service.verify_refresh_token(refresh_token)
        except Exception as exc:
            logger.exception("Error verifying refresh token")
            return JsonResponse({"error": str(exc)}, status=400)

        user_id = refresh_payload["sub"]
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error("User from refresh token not found", extra={"user_id": user_id})
            return JsonResponse({"error": "User not found"}, status=400)

        if not user.is_active:
            logger.error(
                "User from refresh token is not active anymore", extra={"user_id": user_id}
            )
            return JsonResponse({"error": "User not found"}, status=400)

        access_token, refresh_token = terraso_login(self.request, user)

        return JsonResponse(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
        )


class LogoutView(View):
    def post(self, request, *args, **kwargs):
        dj_logout(request)
        return HttpResponse("OK", status=200)


def terraso_login(request, user):
    access_token = jwt_service.create_access_token(user)
    refresh_token = jwt_service.create_refresh_token(user)
    dj_login(request, user, backend="django.contrib.auth.backends.ModelBackend")

    return access_token, refresh_token


class TokenExchangeView(View):
    @staticmethod
    def _create_or_fetch_user(
        email: str = "",
        given_name: str = "",
        family_name: str = "",
        picture: Optional[str] = None,
        **kwargs,
    ):
        account_service = AccountService()
        additional_kwargs = {}
        if picture:
            additional_kwargs["profile_image_url"] = picture
        # TODO: using a private method of AccountService is weird, should be refactored
        # Should be a public method, and arguably static
        user, created = account_service._persist_user(
            email, first_name=given_name, last_name=family_name, **additional_kwargs
        )
        return user, created

    @staticmethod
    def _check_request(contents):
        missing_keys = []
        for key in ("jwt", "provider"):
            if key not in contents:
                missing_keys.append(key)
        if missing_keys:
            return JsonResponse({"missing_keys": missing_keys}, status=400)
        provider = contents["provider"]
        if provider not in settings.JWT_EXCHANGE_PROVIDERS:
            return JsonResponse({"bad_provider": provider}, status=400)

    @staticmethod
    def _token_error(e):
        match e.error_type:
            case "jwks_error" | "bad_config":
                status_code = 500
            case "token_error":
                status_code = 400
            case _:
                status_code = 500
        return JsonResponse({e.error_type: e.message}, status=status_code)

    def post(self, request, *args, **kwargs):
        contents = json.loads(request.body)
        if resp := self._check_request(contents):
            return resp

        try:
            tokex_service = TokenExchangeService.from_payload(contents, settings)
            payload = tokex_service.validate()
        except TokenExchangeException as e:
            return self._token_error(e)

        user, created = self._create_or_fetch_user(**payload)
        access_token, refresh_token = terraso_login(request, user)
        resp_payload = {
            "rtoken": refresh_token,
            "atoken": access_token,
        }

        if created:
            resp_payload["created"] = True
        return JsonResponse(resp_payload)
