from django.contrib import admin
from .models import Subject, Topic, Question, Answer, UserAnswer, UserTopicProgress, SessionQuestion, QuestionSession

admin.site.register(Subject)
admin.site.register(Topic)



# Javoblar - Inline ko‘rinishda (Savol ichida ko‘rsatish)
class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 2


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text_short', 'topic', 'created_by', 'created_at')
    list_filter = ('topic', 'created_by')
    search_fields = ('question_text',)
    inlines = [AnswerInline]
    readonly_fields = ('created_at', 'updated_at', 'slug')

    def question_text_short(self, obj):
        return obj.question_text[:50]
    question_text_short.short_description = "Savol"


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('answer_text_short', 'question', 'is_correct', 'created_at')
    list_filter = ('is_correct',)
    search_fields = ('answer_text',)
    readonly_fields = ('created_at', 'updated_at')

    def answer_text_short(self, obj):
        return obj.answer_text[:50]
    answer_text_short.short_description = "Javob"


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('user', 'question_short', 'is_correct', 'created_at')
    list_filter = ('is_correct', 'created_at')
    search_fields = ('user__username', 'question__question_text')
    readonly_fields = ('created_at',)

    def question_short(self, obj):
        return obj.question.question_text[:50]
    question_short.short_description = "Savol"


@admin.register(UserTopicProgress)
class UserTopicProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'topic', 'correct_answers', 'incorrect_answers', 'total_questions', 'last_updated')
    list_filter = ('topic',)
    search_fields = ('user__username', 'topic__name')
    readonly_fields = ('last_updated',)


class SessionQuestionInline(admin.TabularInline):
    model = SessionQuestion
    extra = 0
    readonly_fields = ('question', 'selected_answer', 'is_correct')


@admin.register(QuestionSession)
class QuestionSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'topic', 'is_completed', 'correct_count', 'incorrect_count', 'started_at', 'completed_at', 'total_questions')
    list_filter = ('is_completed', 'topic')
    search_fields = ('user__username', 'topic__name')
    readonly_fields = ('started_at', 'completed_at')
    inlines = [SessionQuestionInline]


@admin.register(SessionQuestion)
class SessionQuestionAdmin(admin.ModelAdmin):
    list_display = ('session', 'question_short', 'selected_answer', 'is_correct')
    list_filter = ('is_correct',)
    search_fields = ('session__user__username', 'question__question_text')

    def question_short(self, obj):
        return obj.question.question_text[:50]
    question_short.short_description = "Savol"