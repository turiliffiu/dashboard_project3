from django.shortcuts import render
from django.http import JsonResponse, FileResponse, Http404 
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import ProcedureCategory
from .decorators import role_required, ajax_login_required, can_edit_procedure, can_delete_procedure
import os
import json
import mimetypes

@login_required
def dashboard(request):
    """Vista principale della dashboard"""
    # Filtra le categorie in base ai permessi
    if request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin'):
        # Admin vede tutto
        categories = ProcedureCategory.objects.all()
    else:
        # Altri vedono solo pubbliche o proprie
        categories = ProcedureCategory.objects.filter(
            is_public=True
        ) | ProcedureCategory.objects.filter(owner=request.user)
        categories = categories.distinct()
    
    # Aggiungi informazioni sui permessi per ogni categoria
    categories_with_perms = []
    for cat in categories:
        categories_with_perms.append({
            'category': cat,
            'can_edit': cat.can_user_edit(request.user),
            'can_delete': cat.can_user_delete(request.user)
        })
    
    return render(request, 'procedures/dashboard.html', {
        'categories': categories_with_perms,
        'user': request.user
    })

@ajax_login_required
def get_procedure_content(request, filename):
    """API per ottenere il contenuto di un file di procedura"""
    try:
        file_path = os.path.join(settings.PROCEDURE_FILES_DIR, filename)
        
        # Verifica che il file esista e sia nella cartella corretta
        if not os.path.exists(file_path):
            return JsonResponse({'error': 'File non trovato'}, status=404)
        
        # Verifica che il percorso sia sicuro (previene path traversal)
        if not os.path.abspath(file_path).startswith(str(settings.PROCEDURE_FILES_DIR)):
            return JsonResponse({'error': 'Accesso negato'}, status=403)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parsa il contenuto del file
        sections = parse_procedure_file(content)
        
        return JsonResponse({
            'success': True,
            'sections': sections
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@role_required('admin', 'editor')
def upload_procedure_file(request):
    """API per caricare un nuovo file di procedura"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non consentito'}, status=405)
    
    try:
        # Verifica che ci sia un file
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'Nessun file caricato'}, status=400)
        
        uploaded_file = request.FILES['file']
        
        # Verifica estensione .txt
        if not uploaded_file.name.endswith('.txt'):
            return JsonResponse({'error': 'Solo file .txt sono consentiti'}, status=400)
        
        # Sanitizza il nome del file
        filename = uploaded_file.name.replace(' ', '_')
        filename = ''.join(c for c in filename if c.isalnum() or c in '._-')
        
        # Verifica che il file non esista già
        file_path = os.path.join(settings.PROCEDURE_FILES_DIR, filename)
        if os.path.exists(file_path):
            return JsonResponse({'error': 'Un file con questo nome esiste già'}, status=400)
        
        # Salva il file
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        # Ottieni i dati aggiuntivi
        name = request.POST.get('name', filename.replace('.txt', '').replace('_', ' ').title())
        icon = request.POST.get('icon', '📄')
        description = request.POST.get('description', '')
        is_public = request.POST.get('is_public', 'true').lower() == 'true'
        
        # Crea la categoria nel database con owner
        category = ProcedureCategory.objects.create(
            name=name,
            icon=icon,
            description=description,
            filename=filename,
            order=ProcedureCategory.objects.count() + 1,
            owner=request.user,
            is_public=is_public
        )
        
        return JsonResponse({
            'success': True,
            'message': 'File caricato con successo',
            'category': {
                'id': category.id,
                'name': category.name,
                'icon': category.icon,
                'description': category.description,
                'filename': category.filename,
                'owner': category.owner.username if category.owner else None,
                'is_public': category.is_public
            }
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@can_edit_procedure
def update_procedure_category(request, category_id):
    """API per aggiornare una categoria esistente"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non consentito'}, status=405)
    
    try:
        category = ProcedureCategory.objects.get(id=category_id)
        
        # Aggiorna i campi
        if 'name' in request.POST:
            category.name = request.POST['name']
        if 'icon' in request.POST:
            category.icon = request.POST['icon']
        if 'description' in request.POST:
            category.description = request.POST['description']
        if 'is_public' in request.POST:
            category.is_public = request.POST['is_public'].lower() == 'true'
        
        category.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Categoria aggiornata con successo',
            'category': {
                'id': category.id,
                'name': category.name,
                'icon': category.icon,
                'description': category.description,
                'filename': category.filename,
                'is_public': category.is_public
            }
        })
    
    except ProcedureCategory.DoesNotExist:
        return JsonResponse({'error': 'Categoria non trovata'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@can_delete_procedure
def delete_procedure_category(request, category_id):
    """API per eliminare una categoria e il suo file"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non consentito'}, status=405)
    
    try:
        category = ProcedureCategory.objects.get(id=category_id)
        
        # Elimina il file dal filesystem
        file_path = os.path.join(settings.PROCEDURE_FILES_DIR, category.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Elimina la categoria dal database
        category_name = category.name
        category.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Categoria "{category_name}" eliminata con successo'
        })
    
    except ProcedureCategory.DoesNotExist:
        return JsonResponse({'error': 'Categoria non trovata'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@can_edit_procedure
def update_procedure_file(request, category_id):
    """API per aggiornare il contenuto del file di procedura"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non consentito'}, status=405)
    
    try:
        category = ProcedureCategory.objects.get(id=category_id)
        
        # Verifica che ci sia un file
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'Nessun file caricato'}, status=400)
        
        uploaded_file = request.FILES['file']
        
        # Verifica estensione .txt
        if not uploaded_file.name.endswith('.txt'):
            return JsonResponse({'error': 'Solo file .txt sono consentiti'}, status=400)
        
        # Sovrascrivi il file esistente
        file_path = os.path.join(settings.PROCEDURE_FILES_DIR, category.filename)
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        return JsonResponse({
            'success': True,
            'message': 'File aggiornato con successo'
        })
    
    except ProcedureCategory.DoesNotExist:
        return JsonResponse({'error': 'Categoria non trovata'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
def parse_procedure_file(content):
    """
    Parsa un file di procedura con formato specifico.
    Supporta comandi su più righe fino alla prossima sezione o comando.

    Formato:
    [SEZIONE]
    Descrizione sezione

    COMANDO: Descrizione comando
    comando riga 1
    comando riga 2
    comando riga 3

    COMANDO: Altro comando
    altro comando
    """
    sections = []
    current_section = None
    lines = content.strip().split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Nuova sezione
        if line.startswith('[') and line.endswith(']'):
            # Salva la sezione precedente se esiste
            if current_section:
                sections.append(current_section)

            section_name = line[1:-1]
            i += 1
            # Leggi la descrizione della sezione (prossima riga non vuota)
            section_desc = ''
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i < len(lines):
                section_desc = lines[i].strip()

            current_section = {
                'title': section_name,
                'desc': section_desc,
                'commands': []
            }

        # Nuovo comando
        elif line.startswith('COMANDO:'):
            label = line.replace('COMANDO:', '').strip()
            i += 1

            # Raccogli tutte le righe del comando fino al prossimo COMANDO: o [SEZIONE]
            cmd_lines = []
            while i < len(lines):
                next_line = lines[i].strip()

                # Stop se troviamo una nuova sezione o comando
                if (next_line.startswith('[') and next_line.endswith(']')) or \
                   next_line.startswith('COMANDO:'):
                    break

                # Aggiungi la riga (anche se vuota, per mantenere la formattazione)
                cmd_lines.append(lines[i].rstrip())
                i += 1

            # Unisci le righe mantenendo i newline
            cmd = '\n'.join(cmd_lines).strip()

            if current_section and cmd:
                current_section['commands'].append({
                    'label': label,
                    'cmd': cmd
                })

            # Decrementa i perché il while principale lo incrementerà
            i -= 1

        i += 1

    # Aggiungi l'ultima sezione se esiste
    if current_section:
        sections.append(current_section)

    return sections

@ajax_login_required
def download_procedure_file(request, category_id):
    """API per scaricare il file di procedura"""
    try:
        category = ProcedureCategory.objects.get(id=category_id)
        file_path = os.path.join(settings.PROCEDURE_FILES_DIR, category.filename)

        # Verifica che il file esista
        if not os.path.exists(file_path):
            raise Http404("File non trovato")

        # Verifica sicurezza path
        if not os.path.abspath(file_path).startswith(str(settings.PROCEDURE_FILES_DIR)):
            raise Http404("Accesso negato")

        # Apri il file e preparalo per il download
        file_handle = open(file_path, 'rb')

        # Determina il mime type
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = 'text/plain'

        # Crea response con il file
        response = FileResponse(file_handle, content_type=mime_type)
        response['Content-Disposition'] = f'attachment; filename="{category.filename}"'

        return response

    except ProcedureCategory.DoesNotExist:
        raise Http404("Categoria non trovata")
    except Exception as e:
        raise Http404(f"Errore: {str(e)}")
