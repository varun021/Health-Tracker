from django.contrib import admin
from .models import (
    Disease, Symptom, DiseaseSymptom,
    UserSubmission, SubmissionSymptom, DiseasePrediction
)


class DiseaseSymptomInline(admin.TabularInline):
    model = DiseaseSymptom
    extra = 1
    raw_id_fields = ('symptom',)
    fields = ('symptom', 'weight')


@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'description')
    inlines = (DiseaseSymptomInline,)
    list_per_page = 25


@admin.register(Symptom)
class SymptomAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'description')
    list_per_page = 25


@admin.register(DiseaseSymptom)
class DiseaseSymptomAdmin(admin.ModelAdmin):
    list_display = ('disease', 'symptom', 'weight')
    list_filter = ('disease',)
    raw_id_fields = ('disease', 'symptom')
    search_fields = ('disease__name', 'symptom__name')


class SubmissionSymptomInline(admin.TabularInline):
    model = SubmissionSymptom
    extra = 1
    raw_id_fields = ('symptom',)
    fields = ('symptom', 'severity', 'duration', 'onset')


class DiseasePredictionInline(admin.TabularInline):
    model = DiseasePrediction
    extra = 0
    readonly_fields = ('disease', 'confidence_score', 'rank')
    show_change_link = True


@admin.register(UserSubmission)
class UserSubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'primary_prediction', 'severity_category', 'severity_score', 'created_at')
    list_filter = ('severity_category', 'created_at', 'primary_prediction')
    search_fields = ('name', 'user__username', 'primary_prediction__name')
    readonly_fields = ('bmi', 'ip_address', 'user_agent', 'session_id')
    inlines = (SubmissionSymptomInline, DiseasePredictionInline)
    raw_id_fields = ('user', 'primary_prediction')
    list_per_page = 25


@admin.register(SubmissionSymptom)
class SubmissionSymptomAdmin(admin.ModelAdmin):
    list_display = ('submission', 'symptom', 'severity', 'duration', 'onset')
    raw_id_fields = ('submission', 'symptom')
    search_fields = ('submission__name', 'symptom__name')


@admin.register(DiseasePrediction)
class DiseasePredictionAdmin(admin.ModelAdmin):
    list_display = ('submission', 'disease', 'confidence_score', 'rank')
    list_filter = ('disease',)
    raw_id_fields = ('submission', 'disease')
    search_fields = ('submission__name', 'disease__name')
