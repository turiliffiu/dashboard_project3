from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from functools import wraps


def role_required(*roles):
    """
    Decoratore per verificare che l'utente abbia uno dei ruoli specificati
    Uso: @role_required('admin', 'editor')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': 'Autenticazione richiesta'}, status=401)
                from django.shortcuts import redirect
                return redirect('login')
            
            # Superuser ha sempre accesso
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Verifica il ruolo
            if hasattr(request.user, 'profile'):
                if request.user.profile.role in roles:
                    return view_func(request, *args, **kwargs)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Permessi insufficienti'}, status=403)
            from django.shortcuts import render
            return render(request, 'procedures/403.html', status=403)
        
        return wrapper
    return decorator


def ajax_login_required(view_func):
    """
    Decoratore per API che richiede login e ritorna JSON error
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Autenticazione richiesta'}, status=401)
        return view_func(request, *args, **kwargs)
    
    return wrapper


def can_edit_procedure(view_func):
    """
    Decoratore per verificare se l'utente può modificare una procedura specifica
    """
    @wraps(view_func)
    def wrapper(request, category_id, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Autenticazione richiesta'}, status=401)
        
        from .models import ProcedureCategory
        try:
            category = ProcedureCategory.objects.get(id=category_id)
            if not category.can_user_edit(request.user):
                return JsonResponse({'error': 'Non hai i permessi per modificare questa procedura'}, status=403)
            return view_func(request, category_id, *args, **kwargs)
        except ProcedureCategory.DoesNotExist:
            return JsonResponse({'error': 'Categoria non trovata'}, status=404)
    
    return wrapper


def can_delete_procedure(view_func):
    """
    Decoratore per verificare se l'utente può eliminare una procedura specifica
    """
    @wraps(view_func)
    def wrapper(request, category_id, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Autenticazione richiesta'}, status=401)
        
        from .models import ProcedureCategory
        try:
            category = ProcedureCategory.objects.get(id=category_id)
            if not category.can_user_delete(request.user):
                return JsonResponse({'error': 'Non hai i permessi per eliminare questa procedura'}, status=403)
            return view_func(request, category_id, *args, **kwargs)
        except ProcedureCategory.DoesNotExist:
            return JsonResponse({'error': 'Categoria non trovata'}, status=404)
    
    return wrapper
