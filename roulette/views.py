import json
from django.db.models import Prefetch
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from account.models import CustomUser
from roulette.forms import SubjectForm, TopicForm
from django.shortcuts import render, redirect
from .models import Question, Answer, Subject, Topic, UserTopicProgress, UserAnswer, QuestionSession, SessionQuestion, \
    GameLog
from random import shuffle
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db import models
from django.views.generic import ListView, DetailView
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum, Avg
@login_required
def main_view(request):
    # Har bir subject bilan unga tegishli mavzular soni
    subjects = Subject.objects.annotate(topic_count=Count('topics')).order_by('name')

    context = {
        'subjects': subjects,
    }
    return render(request, 'index.html', context)


def subject_topics_view(request, slug):
    subject = get_object_or_404(Subject, slug=slug)

    # Barcha mavzularni olib kelamiz
    topics_qs = subject.topics.all().order_by('name')

    # Qidirish (search)
    query = request.GET.get('q', '')
    if query:
        topics_qs = topics_qs.filter(name__icontains=query)

    # Pagination
    paginator = Paginator(topics_qs, 8)  # Har bir sahifada 8 ta mavzu
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'subject': subject,
        'topics': page_obj,  # sahifadagi mavzular
        'query': query,
        'page_obj': page_obj,
    }
    return render(request, 'subject_topics.html', context)


def topic_detail_main(request, slug):
    """
    Display topic details with user progress, questions, and session information.
    """
    # 1. Get the topic or return 404
    topic = get_object_or_404(
        Topic.objects.select_related('subject'),
        slug=slug
    )

    # 2. Get all questions for the topic with user answers prefetched
    questions = (
        Question.objects
        .filter(topic=topic)
        .order_by('-created_at')
        .prefetch_related(
            Prefetch(
                'user_answers',
                queryset=UserAnswer.objects.filter(user=request.user),
                to_attr='current_user_answers'
            )
        )
    )

    # 3. Pagination - 10 questions per page
    paginator = Paginator(questions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 4. Get user progress for this topic
    user_progress = (
        UserTopicProgress.objects
        .filter(user=request.user, topic=topic)
        .first()
    )

    # 5. Get the latest test session for this user and topic
    question_session = (
        QuestionSession.objects
        .filter(user=request.user, topic=topic)
        .order_by('-started_at')
        .first()
    )

    # 6. Prepare context data
    context = {
        'topic': topic,
        'subject': topic.subject,
        'page_obj': page_obj,
        'total_questions': questions.count(),
        'user_progress': user_progress,
        'question_session': question_session,
        'answered_questions_count': sum(
            1 for q in questions if hasattr(q, 'current_user_answers') and q.current_user_answers
        ),
    }

    return render(request, 'topic_detail_main.html', context)


def prepare_session_questions(session, topic, user, question_limit=10):
    """Foydalanuvchi uchun savollarni tayyorlaydi (javoblar ketma-ketligi aralashgan holda)."""
    answered_ids = UserAnswer.objects.filter(user=user, question__topic=topic, is_correct=True).values_list(
        'question_id', flat=True)
    questions = topic.questions.exclude(id__in=answered_ids).order_by('?')[:question_limit]

    session_questions = []
    for q in questions:
        # Javoblarni olish va ularni aralashtirish
        answers = list(q.answers.all())
        shuffle(answers)

        # SessionQuestion yaratish
        session_question = SessionQuestion.objects.create(session=session, question=q)
        session_questions.append(session_question)

        # Javoblarni cache'ga saqlash yoki boshqa usulda saqlash kerak
        # Chunki keyinroq foydalanuvchiga ko'rsatishda shu aralashgan tartibda chiqarish kerak

    cache.set(f'timer_{user.id}_{topic.slug}', 600, timeout=600)
    return session_questions

@login_required
def question_session(request, slug):
    """Test sessiyasini boshlaydi."""
    topic = get_object_or_404(Topic, slug=slug)
    session, created = QuestionSession.objects.get_or_create(user=request.user, topic=topic, is_completed=False)
    if created:
        prepare_session_questions(session, topic, request.user)
    return render(request, 'question_session.html', {'topic': topic})


@login_required
def get_session_questions_json(request, slug):
    session = get_object_or_404(QuestionSession, user=request.user, topic__slug=slug, is_completed=False)
    questions = []

    for sq in session.session_questions.select_related('question').filter(selected_answer__isnull=True):
        answers = list(sq.question.answers.all())
        shuffle(answers)

        questions.append({
            'id': sq.question.id,
            'question_text': sq.question.question_text,
            'answers': [
                {'id': a.id, 'text': a.answer_text, 'is_correct': a.is_correct} for a in answers
            ],
            'selected_answer_id': None,  # Javob berilmagan, shuning uchun null
            'is_correct': None  # Javob berilmagan, shuning uchun null
        })

    return JsonResponse({'questions': questions})

@login_required
@require_http_methods(["POST"])
def submit_answer(request, slug):
    """Javobni qabul qiladi va ballni yangilaydi."""
    session = get_object_or_404(QuestionSession, user=request.user, topic__slug=slug, is_completed=False)
    data = json.loads(request.body)
    question_id, answer_id = data.get('question_id'), data.get('answer_id')
    session_question = get_object_or_404(SessionQuestion, session=session, question__id=question_id)
    answer = get_object_or_404(Answer, id=answer_id)

    # Javobni saqlash
    session_question.selected_answer = answer
    session_question.is_correct = answer.is_correct
    session_question.save()

    # Sessiya statistikasini yangilash
    session.correct_count = session.session_questions.filter(is_correct=True).count()
    session.incorrect_count = session.session_questions.filter(is_correct=False).count()
    session.save()

    # UserAnswer yangilash yoki yaratish
    UserAnswer.objects.update_or_create(
        user=request.user,
        question=session_question.question,
        defaults={'answer': answer, 'is_correct': answer.is_correct}
    )

    # Ballni yangilash: faqat to'g'ri javobda +1, noto'g'ri javobda o'zgarmaslik
    user = get_user_model().objects.get(id=request.user.id)
    if answer.is_correct:
        user.ball = user.ball + 1
        user.score = user.score + 1
        user.save()

    return JsonResponse({
        'status': 'success',
        'is_correct': answer.is_correct,
        'explanation': getattr(answer, 'explanation', '')
    })

@login_required
def complete_session(request, slug):
    """Sessiyani yakunlaydi."""
    session = get_object_or_404(QuestionSession, user=request.user, topic__slug=slug, is_completed=False)
    session.is_completed = True
    session.completed_at = timezone.now()
    session.save()
    return JsonResponse({'status': 'success', 'redirect_url': reverse('roulette:topic_detail_main', args=[slug])})


# views.py
@login_required
def get_stats(request, slug):
    topic = get_object_or_404(Topic, slug=slug)
    total = topic.questions.count()
    correct = UserAnswer.objects.filter(
        user=request.user,
        question__topic=topic,
        is_correct=True
    ).count()

    return JsonResponse({
        'total': total,
        'correct': correct,
        'percentage': round(correct / total * 100, 2) if total > 0 else 0
    })


@login_required
def sciences_view(request):
    # Barcha fanlarni olish
    subject = Subject.objects.all().order_by('-created_at')
    # Pagination: har bir sahifada 6 ta savol
    paginator = Paginator(subject, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'sciences.html', {
        'page_obj': page_obj,
    })


@login_required
def science_detail(request, slug):
    subject = get_object_or_404(Subject, slug=slug)
    topics = subject.topics.all().annotate(questions_count=Count('questions'))

    # Mavzular soni
    topics_count = topics.count()

    # Savollar soni — barcha mavzular bo‘yicha jami savollar soni
    questions_count = topics.aggregate(total=Sum('questions_count'))['total'] or 0

    if request.method == 'POST':
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.subject = subject
            topic.created_by = request.user
            topic.save()
            messages.success(request, '✅ Yangi mavzu muvaffaqiyatli qo‘shildi!')
            return redirect('roulette:science_detail', slug=subject.slug)
        else:
            messages.error(request, '❌ Mavzuni qo‘shishda xatolik yuz berdi.')
    else:
        form = TopicForm()

    return render(request, 'science_detail.html', {
        'subject': subject,
        'topics': topics,
        'topics_count': topics_count,
        'questions_count': questions_count,
        'form': form,
    })


@login_required
def add_sciences_view(request):
    total_subject = Subject.objects.count()
    total_topic = Topic.objects.count()
    total_question = Question.objects.count()
    total_answer = Answer.objects.count()
    total_user = CustomUser.objects.filter(is_superuser=False).count()

    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save(commit=False)
            subject.created_by = request.user
            subject.save()
            messages.success(request, 'Fan muvaffaqiyatli qo‘shildi')
            return redirect('roulette:sciences_view')
        else:
            print(form.errors)
            messages.error(request, 'Fan qo‘shishda xatolik yuz berdi')
    else:
        form = SubjectForm()

    return render(request, 'add_sciences.html', {
        'form': form,
        'total_subject': total_subject,
        'total_topic': total_topic,
        'total_question': total_question,
        'total_answer': total_answer,
        'total_user': total_user,

    })


def topic_list(request):
    query = request.GET.get('q', '').strip()

    topics = Topic.objects.all().annotate(
        question_count=Count('questions'),
        answer_count=Count('questions__answers')
    )
    if query:
        topics = topics.filter(
            models.Q(name__icontains=query) |
            models.Q(subject__name__icontains=query)
        )

    paginator = Paginator(topics, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Umumiy statistika
    total_topics = Topic.objects.count()
    total_questions = Question.objects.count()
    total_answers = Answer.objects.count()

    context = {
        'page_obj': page_obj,
        'query': query,
        'total_topics': total_topics,
        'total_questions': total_questions,
        'total_answers': total_answers,
    }
    return render(request, 'topic_list.html', context)


def question_list(request):
    query = request.GET.get('q', '').strip()

    questions = Question.objects.all().annotate(
        answer_count=Count('answers')
    )
    if query:
        questions = questions.filter(
            models.Q(question_text__icontains=query) |
            models.Q(topic__name__icontains=query)
        )

    paginator = Paginator(questions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_questions = Question.objects.count()
    total_answers = Answer.objects.count()

    context = {
        'page_obj': page_obj,
        'query': query,
        'total_questions': total_questions,
        'total_answers': total_answers,
    }
    return render(request, 'question_list.html', context)


@login_required
def topic_detail(request, slug):
    topic = get_object_or_404(Topic, slug=slug)

    if request.method == 'POST':
        question_text = request.POST.get('question_text', '').strip()
        if not question_text:
            messages.error(request, "❌ Savol matni bo‘sh bo‘lishi mumkin emas.")
        elif topic.questions.filter(question_text__iexact=question_text).exists():
            messages.error(request, "⚠️ Bu savol allaqachon mavjud.")
        else:
            Question.objects.create(
                topic=topic,
                question_text=question_text,
                created_by=request.user
            )
            messages.success(request, "✅ Yangi savol muvaffaqiyatli qo‘shildi!")
            return redirect('roulette:topic_detail', slug=slug)

    questions = topic.questions.all()
    return render(request, 'topic_detail.html', {
        'topic': topic,
        'questions': questions
    })


@login_required
@require_http_methods(["GET", "POST"])
def question_detail(request, slug):
    question = get_object_or_404(Question, slug=slug)

    if request.method == 'POST':
        answer_text = request.POST.get('answer_text', '').strip()
        is_correct = request.POST.get('is_correct') == 'true'

        if not answer_text:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': "❌ Javob matni bo‘sh bo‘lishi mumkin emas."})
            else:
                messages.error(request, "❌ Javob matni bo‘sh bo‘lishi mumkin emas.")
                return redirect('roulette:question_detail', slug=slug)

        if question.answers.count() >= 10:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse(
                    {'status': 'error', 'message': "❌ Ushbu savol uchun maksimal 10 ta javob kiritilishi mumkin."})
            else:
                messages.error(request, "❌ Ushbu savol uchun maksimal 10 ta javob kiritilishi mumkin.")
                return redirect('roulette:question_detail', slug=slug)

        if is_correct:
            # Barcha eski to‘g‘ri javoblarni noto‘g‘ri qilamiz
            Answer.objects.filter(question=question, is_correct=True).update(is_correct=False)

        Answer.objects.create(
            question=question,
            answer_text=answer_text,
            is_correct=is_correct
        )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': "✅ Yangi javob muvaffaqiyatli qo‘shildi!"})
        else:
            messages.success(request, "✅ Yangi javob muvaffaqiyatli qo‘shildi!")
            return redirect('roulette:question_detail', slug=slug)

    answers = question.answers.all()
    return render(request, 'question_detail.html', {
        'question': question,
        'answers': answers
    })


@login_required
@csrf_exempt
def update_answer(request, answer_id):
    print(f"Received request: method={request.method}, answer_id={answer_id}")

    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        print("AJAX POST request detected")
        try:
            answer = Answer.objects.get(id=answer_id)
            print(
                f"Found answer: id={answer.id}, current_text='{answer.answer_text}', current_is_correct={answer.is_correct}")

            text = request.POST.get('answer_text', '').strip()
            is_correct = request.POST.get('is_correct', 'false') == 'true'
            print(f"Received data: answer_text='{text}', is_correct={is_correct}")

            # Agar yangi javob to'g'ri deb belgilansa, boshqa to'g'ri javoblarni noto'g'ri qilamiz
            if is_correct:
                updated_count = Answer.objects.filter(question=answer.question, is_correct=True).update(
                    is_correct=False)
                print(f"Set {updated_count} other correct answers to False")

            answer.answer_text = text
            answer.is_correct = is_correct
            answer.save()
            print(
                f"Answer updated: id={answer.id}, new_text='{answer.answer_text}', new_is_correct={answer.is_correct}")

            return JsonResponse({'status': 'success', 'message': '✅ Javob yangilandi'})
        except Answer.DoesNotExist:
            print("Answer not found!")
            return JsonResponse({'status': 'error', 'message': '❌ Javob topilmadi'}, status=404)

    print("Invalid request method or headers")
    return JsonResponse({'status': 'error', 'message': '❌ Noto‘g‘ri so‘rov'}, status=400)


@login_required
@csrf_exempt
def delete_answer(request, answer_id):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            answer = Answer.objects.get(id=answer_id)
            answer.delete()
            return JsonResponse({'status': 'success', 'message': '🗑 Javob o‘chirildi'})
        except Answer.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '❌ Javob topilmadi'}, status=404)

    return JsonResponse({'status': 'error', 'message': '❌ Noto‘g‘ri so‘rov'}, status=400)


from django.db.models import Q


class CustomUserListView(ListView):
    model = CustomUser
    template_name = 'user_list.html'  # o'zingizga mos template nomi
    context_object_name = 'users'
    paginate_by = 15  # sahifada nechta foydalanuvchi ko‘rinadi

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        qs = CustomUser.objects.all().order_by('email')

        if query:
            qs = qs.filter(
                Q(email__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(phone_number__icontains=query)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context

class CustomUserDetailView(DetailView):
    model = CustomUser
    template_name = 'user_detail.html'
    context_object_name = 'user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()

        # 1. Umumiy statistika
        user_answers = UserAnswer.objects.filter(user=user)
        total_questions = user_answers.count()
        correct_answers = user_answers.filter(is_correct=True).count()
        incorrect_answers = user_answers.filter(is_correct=False).count()
        correct_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0

        # 2. Fanlar bo'yicha statistika
        subjects_stats = Subject.objects.filter(topics__questions__user_answers__user=user).annotate(
            total_questions=Count('topics__questions__user_answers'),
            correct_answers=Count('topics__questions__user_answers', filter=Q(topics__questions__user_answers__is_correct=True)),
            incorrect_answers=Count('topics__questions__user_answers', filter=Q(topics__questions__user_answers__is_correct=False))
        ).values('name', 'total_questions', 'correct_answers', 'incorrect_answers')

        # 3. Mavzular bo'yicha progress
        topics_stats = UserTopicProgress.objects.filter(user=user).select_related('topic').values(
            'topic__name', 'total_questions', 'correct_answers', 'incorrect_answers'
        )

        # 4. Sessiyalar statistikasi
        sessions = QuestionSession.objects.filter(user=user).select_related('topic')
        total_sessions = sessions.count()
        completed_sessions = sessions.filter(is_completed=True).count()
        sessions_stats = sessions.filter(is_completed=True).annotate(
            total_session_questions=Count('session_questions')
        ).aggregate(
            total_correct=Count('correct_count'),
            total_questions=Count('session_questions')
        )
        avg_correct_percentage = 0
        if sessions_stats['total_correct'] and sessions_stats['total_questions']:
            avg_correct_percentage = (sessions_stats['total_correct'] / sessions_stats['total_questions']) * 100

        # 5. Yakuniy sessiyalar ro'yxati (oxirgi 5 ta)
        recent_sessions = sessions.order_by('-started_at')[:5].values(
            'topic__name', 'is_completed', 'correct_count', 'incorrect_count', 'started_at', 'completed_at'
        )

        # Kontekstga qo'shish
        context.update({
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'incorrect_answers': incorrect_answers,
            'correct_percentage': round(correct_percentage, 2),
            'subjects_stats': subjects_stats,
            'topics_stats': topics_stats,
            'total_sessions': total_sessions,
            'completed_sessions': completed_sessions,
            'avg_correct_percentage': round(avg_correct_percentage, 2),
            'recent_sessions': recent_sessions,
        })

        return context

@login_required
def statistics_view(request):
    user = request.user

    # 1. Umumiy statistika
    user_answers = UserAnswer.objects.filter(user=user)
    total_questions = user_answers.count()
    correct_answers = user_answers.filter(is_correct=True).count()
    incorrect_answers = user_answers.filter(is_correct=False).count()
    correct_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0

    # 2. Fanlar bo'yicha statistika
    subjects_stats = Subject.objects.filter(topics__questions__user_answers__user=user).annotate(
        total_questions=Count('topics__questions__user_answers'),
        correct_answers=Count('topics__questions__user_answers',
                              filter=Q(topics__questions__user_answers__is_correct=True)),
        incorrect_answers=Count('topics__questions__user_answers',
                                filter=Q(topics__questions__user_answers__is_correct=False))
    ).values('name', 'total_questions', 'correct_answers', 'incorrect_answers')

    # 3. Mavzular bo'yicha statistika
    topics_stats = UserTopicProgress.objects.filter(user=user).values(
        'topic__name', 'total_questions', 'correct_answers', 'incorrect_answers'
    )

    # 4. Sessiya statistikasi
    sessions = QuestionSession.objects.filter(user=user)
    total_sessions = sessions.count()
    completed_sessions = sessions.filter(is_completed=True).count()

    # Calculate average correct percentage for completed sessions
    sessions_stats = sessions.filter(is_completed=True).annotate(
        total_session_questions=Count('session_questions')
    ).aggregate(
        avg_correct=Avg('correct_count', output_field=models.FloatField()),
        total_questions=Sum('total_session_questions')
    )

    avg_correct_percentage = 0
    if sessions_stats['avg_correct'] and sessions_stats['total_questions']:
        avg_correct_percentage = (sessions_stats['avg_correct'] / sessions_stats['total_questions']) * 100

    # 5. O'yin loglari statistikasi
    # Eng ko'p xato qilingan savollar
    incorrect_questions = GameLog.objects.filter(user=user, is_correct=False).values(
        'question__question_text'
    ).annotate(
        error_count=Count('question')
    ).order_by('-error_count')[:5]

    # Eng ko'p to'g'ri javob berilgan savollar
    correct_questions = GameLog.objects.filter(user=user, is_correct=True).values(
        'question__question_text'
    ).annotate(
        correct_count=Count('question')
    ).order_by('-correct_count')[:5]

    # Kontekst
    context = {
        'total_questions': total_questions,
        'correct_answers': correct_answers,
        'incorrect_answers': incorrect_answers,
        'correct_percentage': round(correct_percentage, 2),
        'subjects_stats': subjects_stats,
        'topics_stats': topics_stats,
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'avg_correct_percentage': round(avg_correct_percentage, 2),
        'incorrect_questions': incorrect_questions,
        'correct_questions': correct_questions,
    }

    return render(request, 'statistics.html', context)