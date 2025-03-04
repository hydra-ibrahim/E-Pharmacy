from django.contrib.auth.models import User
from rest_framework import serializers
from dj_rest_auth.models import TokenModel

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('is_staff',)


class TokenSerializer(serializers.ModelSerializer):
    """
    Serializer for Token model.
    """
    user = UserSerializer(read_only=True)

    class Meta:
        model = TokenModel
        fields = ('key', 'user')