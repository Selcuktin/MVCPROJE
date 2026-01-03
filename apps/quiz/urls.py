"""Quiz URLs"""
from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    # Teacher views - Question Banks
    path('question-banks/', views.question_bank_list, name='question_bank_list'),
    path('question-banks/create/', views.question_bank_create, name='question_bank_create'),
    path('question-banks/<int:bank_id>/', views.question_bank_detail, name='question_bank_detail'),
    path('question-banks/<int:bank_id>/delete/', views.question_bank_delete, name='question_bank_delete'),
    path('question-banks/<int:bank_id>/add-question/', views.question_create, name='question_create'),
    path('question-banks/<int:bank_id>/bulk-upload/', views.question_bulk_upload, name='question_bulk_upload'),
    path('question/<int:question_id>/edit/', views.question_edit, name='question_edit'),
    path('question/<int:question_id>/delete/', views.question_delete, name='question_delete'),
    
    # Teacher views - Quizzes
    path('all/', views.quiz_list, name='quiz_list'),
    path('create/', views.quiz_create_default, name='quiz_create_default'),
    path('create/<int:group_id>/', views.quiz_create, name='quiz_create'),
    path('<int:quiz_id>/add-questions/', views.quiz_add_questions, name='quiz_add_questions'),
    path('<int:quiz_id>/detail/', views.quiz_detail, name='quiz_detail'),
    path('<int:quiz_id>/edit/', views.quiz_edit, name='quiz_edit'),
    path('<int:quiz_id>/delete/', views.quiz_delete, name='quiz_delete'),
    path('question/<int:question_id>/preview/', views.question_preview, name='question_preview'),
    
    # Student views
    path('available/', views.quiz_list_student, name='quiz_list_student'),
    path('<int:quiz_id>/take/', views.quiz_take, name='quiz_take'),
    path('attempt/<int:attempt_id>/', views.quiz_attempt, name='quiz_attempt'),
    path('attempt/<int:attempt_id>/review/', views.quiz_attempt_review, name='quiz_attempt_review'),
]
