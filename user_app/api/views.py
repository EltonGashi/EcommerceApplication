from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from user_app.api.serializers import RegistrationSerializer
from user_app import models


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    # Delete the authentication token associated with the user
    Token.objects.filter(user=request.user).delete()

    return Response({'detail': 'Logout successful'}, status=status.HTTP_200_OK)

@api_view(['POST',])
def registration_view(request):
    
    if request.method == 'POST':
        serializer = RegistrationSerializer(data=request.data)
        
        data = {}
        
        if serializer.is_valid():
            account = serializer.save()
            
            data['response'] = "Registration Successful!"
            data['username'] = account.username
            data['email'] = account.email
            
            # Use get_or_create to ensure the Token is created if it doesn't exist
            token, created = Token.objects.get_or_create(user=account)
            data['token'] = token.key
            
        else:
            data = serializer.errors
            
        return Response(data, status=status.HTTP_201_CREATED)