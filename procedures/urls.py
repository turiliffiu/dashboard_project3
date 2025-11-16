from django.urls import path
from . import views, auth_views

app_name = 'procedures'

urlpatterns = [
    # Autenticazione
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('register/', auth_views.register_view, name='register'),
    path('profile/', auth_views.profile_view, name='profile'),
    
    # Gestione utenti (solo admin)
    path('users/', auth_views.user_management_view, name='user_management'),
    path('api/users/<int:user_id>/role/', auth_views.update_user_role, name='update_user_role'),
    path('api/users/<int:user_id>/delete/', auth_views.delete_user, name='delete_user'),
    path('api/users/<int:user_id>/toggle-active/', auth_views.toggle_user_active, name='toggle_user_active'),
    
    # Dashboard e procedure
    path('', views.dashboard, name='dashboard'),
    path('api/procedure/<str:filename>/', views.get_procedure_content, name='get_procedure'),
    path('api/upload/', views.upload_procedure_file, name='upload_file'),
    path('api/category/<int:category_id>/update/', views.update_procedure_category, name='update_category'),
    path('api/category/<int:category_id>/delete/', views.delete_procedure_category, name='delete_category'),
    path('api/category/<int:category_id>/update-file/', views.update_procedure_file, name='update_file'),
    path('api/category/<int:category_id>/download/', views.download_procedure_file, name='download_file'), 
]