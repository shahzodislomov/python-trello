from django.urls import path
from .views import SignUpView, VerifyOTPView, SignInView, ToDoView, CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('api/auth/signup/', SignUpView.as_view(), name='signup'),
    path('api/auth/verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('api/auth/signin/', SignInView.as_view(), name='signin'),
    path('api/todos/', ToDoView.as_view(), name='todos'),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('api/auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),

]
