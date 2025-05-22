from django.db import models
from account.models import CustomUser
from django.conf import settings
from django.utils.text import slugify
import uuid  # UUID orqali noyoblikni kafolatlash uchun


class Subject(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)  # Slug maydoni

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='subjects'
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# Mavzu modeli (Fanga bog‘langan)
class Topic(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=150, unique=True, blank=True)  # qo‘shildi
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)  # Django slugify dan import qiling
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.subject.name} - {self.name}"


class Question(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    slug = models.SlugField(max_length=200, unique=True, blank=True)  # ✅ Slug qo‘shildi
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_questions'
    )

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.question_text[:50])
            unique_id = uuid.uuid4().hex[:8]  # qisqa UUID
            self.slug = f"{base_slug}-{unique_id}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.question_text[:50]


# Javob modeli (Savolga bog‘langan)
class Answer(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    answer_text = models.TextField()
    is_correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.answer_text[:50]} ({'To‘g‘ri' if self.is_correct else 'Noto‘g‘ri'})"


class UserAnswer(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_answers'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='user_answers'
    )
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name='user_answers'
    )
    is_correct = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'question']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.question.question_text[:50]}: {'To‘g‘ri' if self.is_correct else 'Noto‘g‘ri'}"


class UserTopicProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='topic_progress'
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='user_progress'
    )
    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    incorrect_answers = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'topic']

    def __str__(self):
        return f"{self.user.username} - {self.topic.name}: {self.correct_answers}/{self.total_questions}"


class QuestionSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    correct_count = models.PositiveIntegerField(default=0)
    incorrect_count = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.user.username} | {self.topic.name} | {'Yakunlangan' if self.is_completed else 'Davom etmoqda'}"

    @property
    def total_questions(self):
        return self.session_questions.count()


class SessionQuestion(models.Model):
    session = models.ForeignKey(QuestionSession, on_delete=models.CASCADE, related_name='session_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(Answer, on_delete=models.SET_NULL, null=True, blank=True)
    is_correct = models.BooleanField(null=True)  # Null => hali tanlanmagan
    answer_order = models.JSONField(null=True, blank=True)  # Javoblar tartibini saqlash
    class Meta:
        unique_together = ['session', 'question']

    def __str__(self):
        status = '✅' if self.is_correct else ('❌' if self.is_correct is False else '⏳')
        return f"{self.session.user.username} | {self.question.id} | {status}"


# O'yin loglari modeli
class GameLog(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='game_logs'
    )  # O'yinchi
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='game_logs'
    )  # Savol
    selected_answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name='selected_game_logs'
    )  # Foydalanuvchi tanlagan javob
    correct_answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name='correct_game_logs'
    )  # To'g'ri javob
    all_answers = models.ManyToManyField(
        Answer,
        related_name='all_game_logs'
    )  # Savoldagi barcha javoblar
    is_correct = models.BooleanField()  # Javob to'g'ri yoki noto'g'ri
    created_at = models.DateTimeField(auto_now_add=True)  # Log vaqti

    class Meta:
        ordering = ['-created_at']  # Yangi loglar yuqorida

    def __str__(self):
        return f"{self.user.email} - {self.question.question_text[:30]}"
