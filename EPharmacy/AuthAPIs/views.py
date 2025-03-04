from django.http.response import HttpResponse as HttpResponse
from django.shortcuts import render

import requests


def InformEmailConfirmation(request, key):

    url = "http://127.0.0.1:8000/api/auth/account-confirm-email/"

    data = {
        "key": key
    }

    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, json=data, headers=headers)

    return render(request, 'AuthAPIs/confirm_template.html', {'response':response})


def PasswordRestConfirmation(request, uidb64, token):

    return render(request, 'AuthAPIs/password reset form.html', {'uidb64':uidb64, 'token':token})
