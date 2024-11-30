from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.views import TokenObtainPairView
# from . import serializers
from .models import User, OTP, ToDo
from .serializers import UserSerializer, ToDoSerializer, CustomTokenObtainPairSerializer
import random
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail


class SignUpView(APIView):
    @swagger_auto_schema(
        request_body=UserSerializer,
        responses={
            201: openapi.Response("User created and OTP sent to email"),
            400: "Invalid data"
        }
    )
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            otp_code = str(random.randint(100000, 999999))
            OTP.objects.create(user=user, code=otp_code)

            send_mail(
                subject="Your OTP Code",
                message=f"Your OTP code is {otp_code}.",
                from_email="your_email@gmail.com",
                recipient_list=[user.email],
                fail_silently=False,
            )

            return Response({"message": "OTP sent to your email"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email'),
                'otp_code': openapi.Schema(type=openapi.TYPE_STRING, description='OTP code')
            },
            required=['email', 'otp_code']
        ),
        responses={
            200: openapi.Response("OTP verified successfully with access token"),
            400: "Invalid OTP",
            404: "User not found"
        }
    )
    def post(self, request):
        email = request.data.get('email')
        otp_code = request.data.get('otp_code')
        try:
            user = User.objects.get(email=email)
            otp = OTP.objects.filter(user=user, code=otp_code).first()
            if otp:
                user.is_verified = True
                user.save()
                otp.delete()
                # Generate JWT token
                refresh = RefreshToken.for_user(user)
                return Response({
                    "message": "OTP verified successfully",
                    "access_token": str(refresh.access_token)
                }, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)


# Sign-In View
class SignInView(APIView):
    @swagger_auto_schema(
        operation_description="User login to obtain access token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email address'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='User password'),
            },
            required=['email', 'password']
        ),
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example="Login successful"),
                        'access_token': openapi.Schema(type=openapi.TYPE_STRING, example="eyJ0eXAiOiJKV1QiLCJh..."),
                    }
                )
            ),
            401: openapi.Response(
                description="Invalid credentials",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example="Invalid credentials"),
                    }
                )
            )
        }
    )
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(email=email, password=password)

        if user and user.is_verified:
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Login successful",
                "access_token": str(refresh.access_token)
            }, status=status.HTTP_200_OK)

        return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


class ToDoView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=ToDoSerializer,
        responses={201: ToDoSerializer, 400: "Invalid data"}
    )
    def post(self, request):
        try:
            serializer = ToDoSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'filter',
                openapi.IN_QUERY,
                description="Filter tasks by 'daily', 'weekly', or 'monthly'",
                type=openapi.TYPE_STRING
            )
        ],
        responses={200: ToDoSerializer(many=True)}
    )
    def get(self, request):
        try:
            filter_type = request.query_params.get('filter')
            todos = ToDo.objects.filter(user=request.user)
            if filter_type == 'daily':
                todos = todos.filter(due_date__day=datetime.today().day)
            elif filter_type == 'weekly':
                todos = todos.filter(due_date__week=datetime.today().isocalendar()[1])
            elif filter_type == 'monthly':
                todos = todos.filter(due_date__month=datetime.today().month)

            serializer = ToDoSerializer(todos, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        request_body=ToDoSerializer,
        responses={200: ToDoSerializer, 404: "Not found", 400: "Invalid data"}
    )
    def put(self, request, pk):
        try:
            todo = ToDo.objects.filter(pk=pk, user=request.user).first()
            if not todo:
                return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

            serializer = ToDoSerializer(todo, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        responses={204: "Successfully deleted", 404: "Not found"}
    )
    def delete(self, request, pk):
        try:
            todo = ToDo.objects.filter(pk=pk, user=request.user).first()
            if not todo:
                return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

            todo.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
