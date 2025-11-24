from django.urls import path
from . import views, auth_views

app_name = 'procedures'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Autenticazione
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('register/', auth_views.register_view, name='register'),
    path('profile/', auth_views.profile_view, name='profile'),
    
    # Gestione Utenti (solo Admin)
    path('users/', auth_views.user_management_view, name='user_management'),
    path('api/user/<int:user_id>/update-role/', auth_views.update_user_role, name='update_user_role'),
    path('api/user/<int:user_id>/delete/', auth_views.delete_user, name='delete_user'),
    path('api/user/<int:user_id>/toggle-active/', auth_views.toggle_user_active, name='toggle_user_active'),

    # API WYSIWYG Editor
    path('api/procedure/create-wysiwyg/', views.create_procedure_wysiwyg, name='create_procedure_wysiwyg'),
    path('api/category/<int:category_id>/update-wysiwyg/', views.update_procedure_wysiwyg, name='update_procedure_wysiwyg'),
    
    # API Procedure - Lettura
    path('api/procedure/<str:filename>/', views.get_procedure_content, name='get_procedure_content'),
    path('api/category/<int:category_id>/download/', views.download_procedure_file, name='download_procedure'),
    
    # API Procedure - Scrittura (Upload tradizionale)
    path('api/upload/', views.upload_procedure_file, name='upload_procedure'),
    path('api/category/<int:category_id>/update/', views.update_procedure_category, name='update_category'),
    path('api/category/<int:category_id>/delete/', views.delete_procedure_category, name='delete_category'),
    path('api/category/<int:category_id>/update-file/', views.update_procedure_file, name='update_file'),
    path('api/category/<int:category_id>/update-command/', views.update_single_command, name='update_single_command'),
    
    # API Ricerca Full-Text
    path('api/search/', views.search_procedures, name='search_procedures'),
]
