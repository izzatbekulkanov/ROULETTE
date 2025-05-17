from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser
from .serializers import RegisterSerializer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


@csrf_exempt
def login_view(request):
    print(f"Login view called with method: {request.method}")
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(f"Login POST data: {data}")
            email_or_username = data.get('email_or_username')
            password = data.get('password')

            if not email_or_username or not password:
                print("Error: Email/username or password missing")
                return JsonResponse({
                    'message': 'Kirish muvaffaqiyatsiz',
                    'errors': {'error': 'Email/foydalanuvchi nomi va parol kiritilishi shart'}
                }, status=400)

            user = None
            if '@' in email_or_username:
                print(f"Attempting login with email: {email_or_username}")
                try:
                    user_obj = CustomUser.objects.get(email=email_or_username)
                    print(f"Email found in database: {user_obj.email}")
                    user = authenticate(request, email=email_or_username, password=password)
                    print(f"Authenticate result for email: {user}")
                except CustomUser.DoesNotExist:
                    print(f"Email not found: {email_or_username}")
                    return JsonResponse({
                        'message': 'Kirish muvaffaqiyatsiz',
                        'errors': {'error': 'Email mavjud emas'}
                    }, status=401)
            else:
                print(f"Attempting login with username: {email_or_username}")
                try:
                    user_obj = CustomUser.objects.get(username=email_or_username)
                    print(f"Username found in database: {user_obj.username}, associated email: {user_obj.email}")
                    user = authenticate(request, email=user_obj.email, password=password)
                    print(f"Authenticate result for username: {user}")
                except CustomUser.DoesNotExist:
                    print(f"Username not found: {email_or_username}")
                    return JsonResponse({
                        'message': 'Kirish muvaffaqiyatsiz',
                        'errors': {'error': 'Foydalanuvchi nomi mavjud emas'}
                    }, status=401)

            if user is None:
                print(f"Authentication failed for email/username: {email_or_username}")
                return JsonResponse({
                    'message': 'Kirish muvaffaqiyatsiz',
                    'errors': {'error': 'Noto‘g‘ri email/foydalanuvchi nomi yoki parol'}
                }, status=401)

            print(f"User authenticated: {user.email}")
            login(request, user)
            refresh = RefreshToken.for_user(user)
            print(f"Tokens generated for user: {user.email}")
            return JsonResponse({
                'message': 'Kirish muvaffaqiyatli',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'email': user.email,
                    'first_name': user.first_name,
                    'role': user.role
                }
            }, status=200)

        except json.JSONDecodeError:
            print("Error: Invalid JSON data in login POST")
            return JsonResponse({
                'message': 'Xato yuz berdi',
                'errors': {'error': 'Noto‘g‘ri JSON formati'}
            }, status=400)
        except Exception as e:
            print(f"Unexpected error during login: {str(e)}")
            return JsonResponse({
                'message': 'Xato yuz berdi',
                'errors': {'error': f'Noma’lum xato: {str(e)}'}
            }, status=500)

    print("Rendering login template")
    return render(request, 'account/login.html')


@csrf_exempt
def register_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            email = data.get('email')
            username = data.get('username')
            password = data.get('password')

            if not (first_name and last_name and email and username and password):
                return JsonResponse({'message': 'Barcha maydonlar to‘ldirilishi shart'}, status=400)

            if CustomUser.objects.filter(username=username).exists():
                return JsonResponse({'message': 'Foydalanuvchi nomi allaqachon mavjud'}, status=400)

            if CustomUser.objects.filter(email=email).exists():
                return JsonResponse({'message': 'Email allaqachon mavjud'}, status=400)

            user = CustomUser.objects.create_user(username=username, email=email, password=password,
                                                  first_name=first_name,
                                                  last_name=last_name)
            return JsonResponse({'message': 'Ro‘yxatdan o‘tish muvaffaqiyatli'}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'message': 'Noto‘g‘ri JSON formati'}, status=400)

    return render(request, 'account/register.html')


# Username mavjudligini tekshirish
@csrf_exempt
def check_username(request):
    print(f"Check username called with method: {request.method}")
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(f"Check username POST data: {data}")
            username = data.get('username')
            if not username:
                print("Error: Username not provided")
                return JsonResponse({
                    'message': 'Xato yuz berdi',
                    'errors': {'username': 'Foydalanuvchi nomi kiritilmadi'}
                }, status=400)

            exists = CustomUser.objects.filter(username=username).exists()
            print(f"Username {username} exists: {exists}")
            return JsonResponse({
                'message': 'Tekshiruv muvaffaqiyatli',
                'available': not exists
            }, status=200)

        except json.JSONDecodeError:
            print("Error: Invalid JSON data in check username POST")
            return JsonResponse({
                'message': 'Xato yuz berdi',
                'errors': {'error': 'Noto‘g‘ri ma’lumot formati'}
            }, status=400)

    return JsonResponse({
        'message': 'Faqat POST so‘rovi qabul qilinadi',
        'errors': {'error': 'Noto‘g‘ri so‘rov turi'}
    }, status=405)


def logout_view(request):
    logout(request)
    return JsonResponse({'message': 'Tizimdan chiqish muvaffaqiyatli'}, status=200)
