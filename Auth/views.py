import datetime
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Doctors
from django.db import IntegrityError
from django.contrib.auth.hashers import check_password
import jwt
from django.core.exceptions import ObjectDoesNotExist



# SignUp function 
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from django.conf import settings
import jwt, datetime
from .models import Doctors

@api_view(['POST'])
def SignUp(request):
    try:
        email = request.data.get("email")
        password = request.data.get("password")

        # Basic validation
        if not email or not password:
            return Response({
                "message": "All fields are required.",
                "access_token": ""
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if user already exists
        user = Doctors.objects.get(email=email)
        return Response({
                "message": "Email already registered.",
                "access_token": ""
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except ObjectDoesNotExist as e : 
        # Create user
            user = Doctors.objects.create_user(
                email=email,
                password=password
            )

            # Create JWT token
            payload = {
                'id': user.id,
                'email': user.email,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=100),
                'iat': datetime.datetime.utcnow()
            }

            token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

            return Response({
                "message": "SignUp successful",
                "access_token": token
            }, status=status.HTTP_201_CREATED)

    except IntegrityError:
        return Response({
            "message": "Database error. Try again.",
            "access_token": ""
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        return Response({
            "message": f"Error: {str(e)}",
            "access_token": ""
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# crate the view for the login
@api_view(['POST']) 
def Login(request) : 
    email = request.data.get('email')
    password = request.data.get('password')

    # check if the use exists 
    try : 
        user = Doctors.objects.get(email=email)
        #check the password
        check = check_password(password, user.password)
        if check : 
            # create the JWT 
            payload = {
                'id': user.id,
                'email': user.email,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=100),
                'iat': datetime.datetime.utcnow()
                }

            token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
            return Response({
                            "message" : "Logged in successfully", 
                            "access_token" : token,
                                },status=status.HTTP_200_OK)
        if not check : 
                return Response({
                    "message" : "Wrong Credentials", 
                    "access_token" : ""
                    },status=status.HTTP_400_BAD_REQUEST)
    except ObjectDoesNotExist as e : 
        return Response({
                "message" : "haha wrong credentials", 
                "access_token" : ""
                },status=status.HTTP_400_BAD_REQUEST)
    except Exception as e : 
        return Response({ 
          "message":f"exception : {str(e)}",
          "access_token" : ""},status=status.HTTP_400_BAD_REQUEST)
    