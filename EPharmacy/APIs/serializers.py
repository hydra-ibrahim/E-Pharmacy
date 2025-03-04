from datetime import datetime, timedelta
import time
from EPharmacy.settings import TIME_INPUT_FORMATS
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import BusinessHours, Pharmacy, User


class PharmacistSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=150, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']


class BusinessHoursSerializer(serializers.ModelSerializer):

    def to_internal_value(self, data):
        
        # Convert empty strings to None for opened_at
        if 'opened_at' in data and data['opened_at'] == '':
            data['opened_at'] = None

        if 'closed_at' in data and data['closed_at'] == '':
            data['closed_at'] = None

        return super().to_internal_value(data)

    def validate(self, attrs):
        
        if attrs['opened_at'] == None and attrs['closed_at'] != None:
            raise serializers.ValidationError('You should specify a value for opened_at field on %s!' % attrs['day_of_the_week'])
        
        elif attrs['opened_at'] != None and attrs['closed_at'] == None:
            raise serializers.ValidationError('You should specify a value for closed_at field on %s!' % attrs['day_of_the_week'])
        
        elif attrs['opened_at'] != attrs['closed_at'] != None and attrs['opened_at'] > attrs['closed_at']:
            raise serializers.ValidationError('opens time must be before closes time on %s!' % attrs['day_of_the_week'])

        return super().validate(attrs)

    opened_at = serializers.TimeField(format=TIME_INPUT_FORMATS[-1], input_formats=TIME_INPUT_FORMATS, required=False, allow_null=True)
    closed_at = serializers.TimeField(format=TIME_INPUT_FORMATS[-1], input_formats=TIME_INPUT_FORMATS, required=False, allow_null=True)

    class Meta:
        model = BusinessHours
        fields = ['day_of_the_week', 'opened_at', 'closed_at']
        validators = []  # Remove a default "unique together" constraint.


class PharmacySerializer(GeoFeatureModelSerializer):
    """ A class to serialize locations as GeoJSON compatible data """

    def validate_business_hours(self, business_hours):

        if len(business_hours) > 7:
            raise serializers.ValidationError('There are not more than 7 days a week!\nYou must have duplicated some days!')
        
        week_days = []
        for day_of_the_week_business_hours in business_hours:
            week_days += [day_of_the_week_business_hours['day_of_the_week']]
        
        if len(week_days) > len(set(week_days)):
            raise serializers.ValidationError('You have duplicated week days!')
        
        return business_hours

    pharmacist = PharmacistSerializer()
    business_hours = BusinessHoursSerializer(many=True)

    class Meta:
        model = Pharmacy
        geo_field = "location"
        
        fields = ('name', 'pharmacist', 'phone_number', 'email', 'business_hours')

    def create(self, validated_data):

        return Pharmacy.objects.create_pharmacy(
            name=validated_data['name'], pharmacist=validated_data['pharmacist'], 
            phone_number=validated_data['phone_number'], email=validated_data['email'], 
            business_hours=validated_data['business_hours'], location=validated_data['location']
        )
