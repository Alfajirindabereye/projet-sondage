from django.contrib import admin
from .models import Survey, Question, Choice, Response, Answer


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 0


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fk_name = 'survey'


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'status_label', 'response_count', 'created_at', 'expires_at')
    list_filter = ('is_closed',)
    search_fields = ('title', 'owner__username')
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'survey', 'question_type', 'order', 'required')
    inlines = [ChoiceInline]


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('survey', 'respondent', 'submitted_at')


admin.site.register(Choice)
admin.site.register(Answer)
