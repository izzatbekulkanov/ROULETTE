from rest_framework import serializers
from .models import CustomUser


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'third_name', 'email', 'username', 'password', 'password_confirm']

    def validate(self, data):
        print(f"Validatsiya boshlandi. Kiruvchi ma'lumotlar: {data}")

        # Parolni tasdiqlash
        if data['password'] != data['password_confirm']:
            print("Xato: Parollar mos emas")
            raise serializers.ValidationError({"password_confirm": "Parollar mos emas"})

        # Email noyobligini tekshirish
        email = data.get('email')
        print(f"Email tekshirilmoqda: {email}")
        if CustomUser.objects.filter(email=email).exists():
            print(f"Xato: Email {email} allaqachon ro‘yxatdan o‘tgan")
            raise serializers.ValidationError({"email": "Bu email allaqachon ro‘yxatdan o‘tgan"})

        # Username noyobligini tekshirish
        username = data.get('username')
        print(f"Username tekshirilmoqda: {username}")
        if CustomUser.objects.filter(username=username).exists():
            print(f"Xato: Username {username} allaqachon band")
            raise serializers.ValidationError({"username": "Bu foydalanuvchi nomi band"})

        print("Validatsiya muvaffaqiyatli yakunlandi")
        return data

    def create(self, validated_data):
        print(f"Foydalanuvchi yaratish boshlandi. Tasdiqlangan ma'lumotlar: {validated_data}")
        # Parolni o‘chirib, foydalanuvchi yaratish
        validated_data.pop('password_confirm')
        user = CustomUser.objects.create_user(**validated_data)
        print(f"Foydalanuvchi muvaffaqiyatli yaratildi: {user.email}, ID: {user.id}")
        return user