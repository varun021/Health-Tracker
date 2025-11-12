from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # Skip auth check for login & register
        if request.path in ["/api/users/login/", "/api/users/register/"]:
            return None

        header = self.get_header(request)
        if header is None:
            raw_token = request.COOKIES.get("access_token")
        else:
            raw_token = self.get_raw_token(header)

        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
        except Exception:
            # Expired/invalid tokens shouldn't crash other views
            return None

        return self.get_user(validated_token), validated_token
