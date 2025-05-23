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
    if request.method == 'POST':
        try:
            # JSON ma'lumotlarni o'qish
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'Noto‘g‘ri JSON formati',
                    'errors': {}
                }, status=400)

            email_or_username = data.get('email_or_username', '').strip()
            password = data.get('password', '').strip()

            # Validatsiya
            if not email_or_username or not password:
                return JsonResponse({
                    'success': False,
                    'message': 'Iltimos, barcha maydonlarni to‘ldiring',
                    'errors': {
                        'email_or_username': 'Email yoki foydalanuvchi nomi kiritilishi shart' if not email_or_username else None,
                        'password': 'Parol kiritilishi shart' if not password else None
                    }
                }, status=400)

            # Foydalanuvchini topish va autentifikatsiya qilish
            user = None

            # Email orqali izlash
            if '@' in email_or_username:
                try:
                    user_obj = CustomUser.objects.get(email__iexact=email_or_username)
                    user = authenticate(request, email=user_obj.email, password=password)
                except CustomUser.DoesNotExist:
                    pass
            # Username orqali izlash
            else:
                try:
                    user_obj = CustomUser.objects.get(username__iexact=email_or_username)
                    user = authenticate(request, email=user_obj.email, password=password)
                except CustomUser.DoesNotExist:
                    pass

            # Autentifikatsiya natijasini tekshirish
            if user is None:
                return JsonResponse({
                    'success': False,
                    'message': 'Noto‘g‘ri email/foydalanuvchi nomi yoki parol',
                    'errors': {}
                }, status=401)

            # Agar foydalanuvchi aktiv bo'lmasa
            if not user.is_active:
                return JsonResponse({
                    'success': False,
                    'message': 'Ushbu hisob faol emas',
                    'errors': {}
                }, status=403)

            # Muvaffaqiyatli kirish
            login(request, user)
            refresh = RefreshToken.for_user(user)

            return JsonResponse({
                'success': True,
                'message': 'Kirish muvaffaqiyatli',
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role,
                    'is_active': user.is_active
                }
            }, status=200)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Server xatosi',
                'errors': {'error': str(e)}
            }, status=500)

    # GET so'rovlari uchun HTML sahifasini qaytarish
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
                return JsonResponse({'success': False, 'message': 'Barcha maydonlar to‘ldirilishi shart'}, status=400)

            if CustomUser.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'message': 'Foydalanuvchi nomi allaqachon mavjud'}, status=400)

            if CustomUser.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'message': 'Email allaqachon mavjud'}, status=400)

            # Foydalanuvchini yaratish
            CustomUser.objects.create_user(
                username=username, email=email, password=password,
                first_name=first_name, last_name=last_name
            )

            # Muvaffaqiyatli javob
            return JsonResponse({
                'success': True,
                'message': 'Ro‘yxatdan o‘tish muvaffaqiyatli!',
                'redirect': '/account/login/',
                'tokens': None  # Agar tokenlar kerak bo'lsa, bu yerga qo'shiladi
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Noto‘g‘ri JSON formati'}, status=400)

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
