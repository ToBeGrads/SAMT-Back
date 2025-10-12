import datetime
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Doctors
from django.db import IntegrityError
from django.contrib.auth.hashers import check_password
import jwt


# SignUp function 
@api_view(['POST'])
def SignUp(request):
    try : 
        email = request.data.get("email")
        password = request.data.get("password")

    # Basic validation
        if not email or not password:
            return Response({"status":"!OK","message": "All fields are required.","access_token" : ""}, status=status.HTTP_400_BAD_REQUEST)

    # Check if the user already exists
        if Doctors.objects.filter(email=email).exists():
            return Response({"status":"!OK","message": "Email already registered.","access_token" : ""}, status=status.HTTP_400_BAD_REQUEST)

    # Create user
        user = Doctors.objects.create_user(
        email=email,
        password=password
    )
        
        # create the JWT token 
        payload = {
                    'id': user.id,
                    'email': user.email,
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
                    'iat': datetime.datetime.utcnow()
                    }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        return Response({
            "status" : "OK", 
            "message" : "SignUp successfully", 
            "access_token" : token,

            }, status=status.HTTP_200_OK)
    
    except IntegrityError:
        return Response({"status":"!OK","message": "Database error. Try again.", "access_token" : ""}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({"status":"!OK","message": str(e),"access_token" : ""}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# crate the view for the login
@api_view(['POST']) 
def Login(request) : 
    email = request.data['email']
    password = request.data['password']

    # check if the use exists 
    try : 
        user = Doctors.objects.filter(email=email).exists()
        if user : 
            #checck the password 
            user = Doctors.objects.get(email=email)
            check = check_password(password, user.password)
            if check : 
                # create the JWT 
                payload = {
                    'id': user.id,
                    'email': user.email,
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
                    'iat': datetime.datetime.utcnow()
                    }

                token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
                return Response({"status" : "OK", 
                                 "message" : "Logged in successfully", 
                                "access_token" : token,
                                 },status=status.HTTP_200_OK)
            else : 
                return Response({
                    "status" : "!OK", 
                    "message" : "Wrong Credentials", 
                    "access_token" : ""
                    },status=status.HTTP_400_BAD_REQUEST)
        else : 
            return Response({
                "status" : "!OK",
                "message" : "haha wrong credentials", 
                "access_token" : ""
                },status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e : 
        return Response({
            "status" : "!OK", 
        "message":str(e), "access_token" : ""},status=status.HTTP_400_BAD_REQUEST)
