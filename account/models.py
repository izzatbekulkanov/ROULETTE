from django.db import models
from django.contrib.auth.models import AbstractUser

# Foydalanuvchi rollari uchun konstantalar
class Role(models.TextChoices):
    SUPERADMIN = 'superadmin', 'Superadmin'
    TEACHER = 'teacher', 'O‘qituvchi'
    STUDENT = 'student', 'Talaba'

# Jins uchun konstantalar
class Gender(models.TextChoices):
    MALE = 'male', 'Erkak'
    FEMALE = 'female', 'Ayol'
    OTHER = 'other', 'Boshqa'

# CustomUser modeli
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)  # Email noyob bo‘lishi kerak
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,  # Yangi foydalanuvchilar uchun default rol
    )
    ball = models.IntegerField(default=0)
    score = models.IntegerField(default=0)  # O‘yin ballari
    first_name = models.CharField(max_length=50, blank=True)  # Ism
    last_name = models.CharField(max_length=50, blank=True)  # Familiya
    third_name = models.CharField(max_length=50, blank=True, null=True)  # Otasining ismi
    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        blank=True,  # Jins ixtiyoriy
    )
    birth_date = models.DateField(null=True, blank=True)  # Tug‘ilgan sana
    phone_number = models.CharField(max_length=20, blank=True, null=True)  # Telefon raqami

    # Username o‘rniga email ishlatish uchun
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']  # Admin panelda talab qilinadigan maydonlar

    # groups va user_permissions uchun related_name qo‘shish
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return self.email

    # Rolni tekshirish uchun yordamchi metodlar
    @property
    def is_superadmin(self):
        return self.role == Role.SUPERADMIN

    @property
    def is_teacher(self):
        return self.role == Role.TEACHER

    @property
    def is_student(self):
        return self.role == Role.STUDENT