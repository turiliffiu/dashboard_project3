from django.contrib import admin
from .models import ProcedureCategory, UserProfile

# Register your models here.

@admin.register(ProcedureCategory)
class ProcedureCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'owner', 'is_public', 'filename', 'order', 'created_at']
    list_editable = ['order']
    list_filter = ['is_public', 'owner', 'created_at']
    search_fields = ['name', 'description', 'filename']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'created_at', 'updated_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']