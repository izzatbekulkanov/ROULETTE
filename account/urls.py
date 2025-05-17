from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import login_view, register_view

app_name = 'account'

urlpatterns = [
    path('login/', login_view, name='login'),
    path('signup/', register_view, name='signup'),
    path('logout/', LogoutView.as_view(), name='logout'),  # Logout uchun as_view()
]
