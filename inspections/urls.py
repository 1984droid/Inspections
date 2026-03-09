from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('inspections/', views.inspection_list, name='inspection_list'),
    path('inspections/new/', views.new_inspection, name='new_inspection'),
    path('inspections/<int:inspection_id>/', views.inspection_detail, name='inspection_detail'),
    path('inspections/<int:inspection_id>/answer/<int:question_id>/', views.answer_question, name='answer_question'),
    path('inspections/<int:inspection_id>/test_module/<int:test_module_id>/save/', views.save_test_module_data, name='save_test_module_data'),
    path('inspections/<int:inspection_id>/defect/add/', views.add_defect, name='add_defect'),
    path('inspections/<int:inspection_id>/complete/', views.complete_inspection, name='complete_inspection'),
    path('defects/<int:defect_id>/photo/add/', views.add_defect_photo, name='add_defect_photo'),
    path('customers/new/', views.create_customer, name='create_customer'),
    path('equipment/new/', views.create_equipment, name='create_equipment'),
    path('documents/<int:document_id>/download/', views.download_document, name='download_document'),
]
