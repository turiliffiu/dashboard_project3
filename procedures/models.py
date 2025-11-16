from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class UserProfile(models.Model):
    """Profilo utente esteso con ruoli e permessi"""
    ROLE_CHOICES = [
        ('admin', 'Amministratore'),
        ('editor', 'Editor'),
        ('viewer', 'Visualizzatore'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Profilo Utente"
        verbose_name_plural = "Profili Utente"
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def can_create(self):
        """Editor e Admin possono creare"""
        return self.role in ['admin', 'editor']
    
    def can_edit(self, procedure=None):
        """Admin può modificare tutto, Editor solo le proprie"""
        if self.role == 'admin':
            return True
        if self.role == 'editor' and procedure:
            return procedure.owner == self.user
        return False
    
    def can_delete(self, procedure=None):
        """Admin può eliminare tutto, Editor solo le proprie"""
        if self.role == 'admin':
            return True
        if self.role == 'editor' and procedure:
            return procedure.owner == self.user
        return False
    
    def can_view(self):
        """Tutti possono visualizzare"""
        return True


class ProcedureCategory(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=10)
    description = models.TextField()
    filename = models.CharField(max_length=100)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='procedures', null=True, blank=True)
    is_public = models.BooleanField(default=True, help_text="Se pubblico, tutti possono visualizzare")
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Procedure Categories"
    
    def __str__(self):
        return self.name
    
    def can_user_edit(self, user):
        """Verifica se l'utente può modificare questa procedura"""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if hasattr(user, 'profile'):
            return user.profile.can_edit(self)
        return False
    
    def can_user_delete(self, user):
        """Verifica se l'utente può eliminare questa procedura"""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if hasattr(user, 'profile'):
            return user.profile.can_delete(self)
        return False
