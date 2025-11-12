from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import IntegrityError
import logging
from django.conf import settings

User = get_user_model()
logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """
    User registration endpoint with validation.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        username = request.data.get('username', '').strip()
        email = request.data.get('email', '').strip()
        password = request.data.get('password', '')
        
        # Validate required fields
        if not all([username, email, password]):
            return Response(
                {'error': 'Username, email, and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate username length
        if len(username) < 3:
            return Response(
                {'error': 'Username must be at least 3 characters long'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            return Response(
                {'error': 'Invalid email format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate password strength
        if len(password) < 8:
            return Response(
                {'error': 'Password must be at least 8 characters long'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if username exists
        if User.objects.filter(username__iexact=username).exists():
            return Response(
                {'error': 'Username already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if email exists
        if User.objects.filter(email__iexact=email).exists():
            return Response(
                {'error': 'Email already registered'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email.lower(),
                password=password
            )
            
            logger.info(f"New user registered: {username}")
            
            return Response(
                {
                    'message': 'User registered successfully',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email
                    }
                },
                status=status.HTTP_201_CREATED
            )
        except IntegrityError as e:
            logger.error(f"Registration error: {str(e)}")
            return Response(
                {'error': 'Registration failed. Please try again.'},
                status=status.HTTP_400_BAD_REQUEST
            )


from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.conf import settings
from users.models import User
import logging

logger = logging.getLogger(__name__)

class LoginView(APIView):
    """
    Secure user login endpoint that issues JWT tokens in HttpOnly cookies.
    Handles expired tokens automatically and allows login via username or email.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # 🧹 Step 1 — Always clear old cookies to prevent expired-token issues
        response = Response()
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')

        # Step 2 — Get and validate input
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')

        if not username or not password:
            return Response(
                {'error': 'Username and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Step 3 — Allow login with email or username
        if '@' in username:
            try:
                user_obj = User.objects.get(email__iexact=username)
                username = user_obj.username
            except User.DoesNotExist:
                return Response(
                    {'error': 'Invalid credentials'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

        # Step 4 — Authenticate user
        user = authenticate(request, username=username, password=password)
        if not user:
            logger.warning(f"Failed login attempt for username: {username}")
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'error': 'Account is disabled'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Step 5 — Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        # Step 6 — Prepare cookie settings (different for dev vs prod)
        secure_flag = not getattr(settings, "DEBUG", False)  # True only in production (HTTPS)
        cookie_settings = {
            'httponly': True,
            'secure': secure_flag,
            'samesite': 'Lax' if settings.DEBUG else 'None',  # 'None' for cross-site cookies
            'max_age': 7 * 24 * 60 * 60,  # 7 days
        }

        # Step 7 — Set new cookies
        response.set_cookie('refresh_token', str(refresh), **cookie_settings)
        response.set_cookie('access_token', str(access_token), **cookie_settings)

        # Step 8 — Response payload
        response.data = {
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_verified': getattr(user, 'is_verified', False)
            }
        }

        logger.info(f"User logged in: {username}")
        return response



class LogoutView(APIView):
    """
    User logout endpoint that blacklists refresh token and clears cookies.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()  # Requires 'rest_framework_simplejwt.token_blacklist'
                logger.info(f"User logged out: {request.user.username}")
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
        
        response = Response(
            {'message': 'Logged out successfully'},
            status=status.HTTP_200_OK
        )
        
        # Clear cookies
        response.delete_cookie('access_token', samesite='Lax')
        response.delete_cookie('refresh_token', samesite='Lax')
        
        return response


class MeView(APIView):
    """
    Returns current user information.
    Automatically refreshes access token if expired using refresh cookie.
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        access_token = request.COOKIES.get('access_token')
        refresh_token = request.COOKIES.get('refresh_token')
        
        if not access_token:
            return Response(
                {'error': 'Not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            # Validate access token
            access = AccessToken(access_token)
            user_id = access.get('user_id')
            
            if not user_id:
                raise InvalidToken('Invalid token payload')
            
            user = User.objects.get(id=user_id)
            
            return Response({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_verified': getattr(user, 'is_verified', False),
                'created_at': getattr(user, 'created_at', None),
                'refreshed': False,
            }, status=status.HTTP_200_OK)
            
        except (TokenError, InvalidToken) as e:
            # Access token expired or invalid, try refresh
            if not refresh_token:
                return Response(
                    {'error': 'Authentication expired'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            try:
                refresh = RefreshToken(refresh_token)
                new_access = str(refresh.access_token)
                user_id = refresh.get('user_id')
                
                if not user_id:
                    raise InvalidToken('Invalid refresh token payload')
                
                user = User.objects.get(id=user_id)
                
                # Create response with new access token
                response = Response({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_verified': getattr(user, 'is_verified', False),
                    'created_at': getattr(user, 'created_at', None),
                    'refreshed': True,
                }, status=status.HTTP_200_OK)
                
                # Set new access token cookie
                response.set_cookie(
                    key='access_token',
                    value=new_access,
                    httponly=True,
                    secure=True,
                    samesite='Lax',
                )
                
                logger.info(f"Access token refreshed for user: {user.username}")
                return response
                
            except TokenError as e:
                logger.warning(f"Invalid refresh token: {str(e)}")
                return Response(
                    {'error': 'Invalid or expired refresh token'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class RefreshTokenView(APIView):
    """
    Manually refresh access token using refresh token from cookies.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        
        if not refresh_token:
            return Response(
                {'error': 'Refresh token not found'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            refresh = RefreshToken(refresh_token)
            new_access = str(refresh.access_token)
            
            response = Response(
                {'message': 'Token refreshed successfully'},
                status=status.HTTP_200_OK
            )
            
            response.set_cookie(
                key='access_token',
                value=new_access,
                httponly=True,
                secure=True,
                samesite='Lax',
            )
            
            return response
            
        except TokenError as e:
            logger.warning(f"Token refresh failed: {str(e)}")
            return Response(
                {'error': 'Invalid or expired refresh token'},
                status=status.HTTP_401_UNAUTHORIZED
            )