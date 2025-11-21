from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from .models import UserProfile
from .decorators import role_required

def login_view(request):
    """Vista per il login"""
    if request.user.is_authenticated:
        return redirect('procedures:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # ASSICURA che l'utente abbia un profilo
            from .models import UserProfile
            UserProfile.objects.get_or_create(user=user, defaults={'role': 'viewer'})
            
            messages.success(request, f'Benvenuto, {user.username}!')
            
            # IMPORTANTE: usa reverse per essere sicuro
            from django.urls import reverse
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            else:
                return redirect('procedures:dashboard')
        else:
            messages.error(request, 'Username o password non validi.')
    
    return render(request, 'procedures/login.html')


def logout_view(request):
    """Vista per il logout"""
    from django.contrib import messages as django_messages
    
    # Pulisci tutti i messaggi esistenti prima del logout
    storage = django_messages.get_messages(request)
    for _ in storage:
        pass
    storage.used = True
    
    # Fai logout
    logout(request)
    
    # Aggiungi solo il messaggio di logout
    messages.success(request, 'Logout effettuato con successo.')
    return redirect('procedures:login')




def register_view(request):
    """Vista per la registrazione - disponibile solo se abilitata"""
    # Per sicurezza, disabilitare la registrazione pubblica in produzione
    # e creare utenti solo tramite admin o comando management
    
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Validazione
        if not username or not password1:
            messages.error(request, 'Username e password sono obbligatori.')
            return render(request, 'procedures/register.html')
        
        if password1 != password2:
            messages.error(request, 'Le password non coincidono.')
            return render(request, 'procedures/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username già esistente.')
            return render(request, 'procedures/register.html')
        
        if email and User.objects.filter(email=email).exists():
            messages.error(request, 'Email già registrata.')
            return render(request, 'procedures/register.html')
        
        try:
            # Crea utente
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1
            )
            
            # Crea profilo con ruolo viewer di default
            UserProfile.objects.get_or_create(user=user, defaults={'role': 'viewer'})
            
            messages.success(request, 'Registrazione completata! Ora puoi effettuare il login.')
            return redirect('procedures:login')
        
        except Exception as e:
            messages.error(request, f'Errore durante la registrazione: {str(e)}')
    
    return render(request, 'procedures/register.html')


@login_required
def profile_view(request):
    """Vista per visualizzare e modificare il proprio profilo"""
    user = request.user
    
    # Assicura che l'utente abbia un profilo
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={'role': 'viewer'}
    )
    
    if request.method == 'POST':
        # Aggiorna informazioni profilo
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        
        messages.success(request, 'Profilo aggiornato con successo!')
        return redirect('procedures:profile')
    
    return render(request, 'procedures/profile.html', {
        'user': user,
        'profile': profile
    })


@role_required('admin')
def user_management_view(request):
    """Vista per gestione utenti - solo Admin"""
    users = User.objects.all().select_related('profile').order_by('-date_joined')
    
    return render(request, 'procedures/user_management.html', {
        'users': users
    })


@role_required('admin')
def update_user_role(request, user_id):
    """API per aggiornare il ruolo di un utente - solo Admin"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non consentito'}, status=405)
    
    try:
        user = User.objects.get(id=user_id)
        new_role = request.POST.get('role')
        
        if new_role not in ['admin', 'editor', 'viewer']:
            return JsonResponse({'error': 'Ruolo non valido'}, status=400)
        
        # Non permettere di modificare il proprio ruolo
        if user == request.user:
            return JsonResponse({'error': 'Non puoi modificare il tuo stesso ruolo'}, status=400)
        
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.role = new_role
        profile.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Ruolo di {user.username} aggiornato a {profile.get_role_display()}',
            'user': {
                'id': user.id,
                'username': user.username,
                'role': new_role,
                'role_display': profile.get_role_display()
            }
        })
    
    except User.DoesNotExist:
        return JsonResponse({'error': 'Utente non trovato'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@role_required('admin')
def delete_user(request, user_id):
    """API per eliminare un utente - solo Admin"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non consentito'}, status=405)
    
    try:
        user = User.objects.get(id=user_id)
        
        # Non permettere di eliminare se stesso
        if user == request.user:
            return JsonResponse({'error': 'Non puoi eliminare il tuo stesso account'}, status=400)
        
        # Non permettere di eliminare superuser
        if user.is_superuser:
            return JsonResponse({'error': 'Non puoi eliminare un superuser'}, status=400)
        
        username = user.username
        user.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Utente {username} eliminato con successo'
        })
    
    except User.DoesNotExist:
        return JsonResponse({'error': 'Utente non trovato'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@role_required('admin')
def toggle_user_active(request, user_id):
    """API per attivare/disattivare un utente - solo Admin"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non consentito'}, status=405)
    
    try:
        user = User.objects.get(id=user_id)
        
        if user == request.user:
            return JsonResponse({'error': 'Non puoi disattivare il tuo stesso account'}, status=400)
        
        if user.is_superuser:
            return JsonResponse({'error': 'Non puoi disattivare un superuser'}, status=400)
        
        user.is_active = not user.is_active
        user.save()
        
        status = 'attivato' if user.is_active else 'disattivato'
        
        return JsonResponse({
            'success': True,
            'message': f'Utente {user.username} {status}',
            'user': {
                'id': user.id,
                'username': user.username,
                'is_active': user.is_active
            }
        })
    
    except User.DoesNotExist:
        return JsonResponse({'error': 'Utente non trovato'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
