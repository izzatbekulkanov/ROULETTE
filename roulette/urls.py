from django.urls import path
from .views import main_view, sciences_view, add_sciences_view, science_detail, topic_detail, question_detail, \
    delete_answer, update_answer, topic_list, question_list, CustomUserListView, subject_topics_view, topic_detail_main, \
    question_session, get_session_questions_json, submit_answer, complete_session, statistics_view, \
    CustomUserDetailView, get_stats, update_status, clear_topic_progress

app_name = 'roulette'

urlpatterns = [
    path('', main_view, name='main_admin'),  # Asosiy
    path('statistics/', statistics_view, name='statistics_view'),  # Asosiy
    path('sciences/', sciences_view, name='sciences_view'),
    path('science/<slug:slug>/', science_detail, name='science_detail'),
    path('add-sciences/', add_sciences_view, name='add_sciences_view'),
    path('topics/', topic_list, name='topic_list'),
    path('topic/<slug:slug>/', topic_detail, name='topic_detail'),
    path('question/<slug:slug>/', question_detail, name='question_detail'),
    path('answer/<int:answer_id>/update/', update_answer, name='update_answer'),
    path('answers/<int:answer_id>/delete/', delete_answer, name='delete_answer'),
    path('questions/', question_list, name='question_list'),
    path('users/', CustomUserListView.as_view(), name='user_list'),
    path('user/<int:pk>/', CustomUserDetailView.as_view(), name='user_detail'),
    path('users/<int:user_id>/update_status/', update_status, name='update_status'),
    path('subject/<slug:slug>/', subject_topics_view, name='subject_topics'),
    path('topic-main/<slug:slug>/', topic_detail_main, name='topic_detail_main'),
    path('topic/<slug:slug>/session/', question_session, name='question_session'),
    path('topic/<slug:slug>/questions-json/', get_session_questions_json, name='get_session_questions_json'),
    path('topic/<slug:slug>/submit-answer/', submit_answer, name='submit_answer'),  #
    path('topic/<slug:slug>/complete/', complete_session, name='complete_session'),
    path('topic/<slug:slug>/stats/', get_stats, name='get_stats'),
    path('clear-progress/<slug:slug>/', clear_topic_progress, name='clear_topic_progress'),
]
