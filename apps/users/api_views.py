"""
API Views for JWT Authentication
Bu dosya JWT token tabanlı authentication için endpoint'leri sağlar.
Mobil uygulamalar ve API istemcileri için kullanılır.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from .models import User, UserProfile


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer - token'a ek bilgiler ekler
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Token'a custom claims ekle
        token['username'] = user.username
        token['email'] = user.email
        
        if hasattr(user, 'userprofile'):
            token['user_type'] = user.userprofile.user_type
        
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Response'a ek bilgiler ekle
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
        }
        
        if hasattr(self.user, 'userprofile'):
            data['user']['user_type'] = self.user.userprofile.user_type
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    JWT Token endpoint - Giriş için kullanılır
    POST /api/token/
    {
        "username": "user1",
        "password": "pass123"
    }
    """
    serializer_class = CustomTokenObtainPairSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register_api(request):
    """
    API üzerinden kullanıcı kaydı
    POST /api/register/
    {
        "username": "newuser",
        "email": "user@example.com",
        "password": "securepass",
        "first_name": "John",
        "last_name": "Doe"
    }
    """
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    
    if not username or not email or not password:
        return Response(
            {'error': 'Username, email ve password gereklidir'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'Bu kullanıcı adı zaten kullanılıyor'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if User.objects.filter(email=email).exists():
        return Response(
            {'error': 'Bu email zaten kullanılıyor'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Kullanıcı oluştur
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )
    
    # User profile oluştur
    UserProfile.objects.create(
        user=user,
        user_type='student'  # Default student
    )
    
    # JWT token oluştur
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'message': 'Kullanıcı başarıyla oluşturuldu',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        },
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    """
    API üzerinden çıkış - Refresh token'ı blacklist'e ekler
    POST /api/logout/
    {
        "refresh": "refresh_token_here"
    }
    """
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response(
            {'message': 'Başarıyla çıkış yapıldı'},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile_api(request):
    """
    Mevcut kullanıcının profil bilgilerini döner
    GET /api/profile/
    """
    user = request.user
    
    profile_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
    }
    
    if hasattr(user, 'userprofile'):
        profile_data['user_type'] = user.userprofile.user_type
        profile_data['phone'] = user.userprofile.phone
        profile_data['bio'] = user.userprofile.bio
    
    return Response(profile_data)

