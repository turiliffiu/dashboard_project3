from django.shortcuts import render
from django.http import JsonResponse, FileResponse, Http404 
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Q
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
def search_procedures(request):
    """API per ricerca full-text nelle procedure"""
    try:
        query = request.GET.get('q', '').strip()
        
        if not query or len(query) < 2:
            return JsonResponse({
                'success': False,
                'message': 'Query troppo corta (minimo 2 caratteri)'
            })
        
        # Determina quali categorie l'utente può vedere
        if request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin'):
            categories = ProcedureCategory.objects.all()
        else:
            categories = ProcedureCategory.objects.filter(
                Q(is_public=True) | Q(owner=request.user)
            ).distinct()
        
        results = []
        
        # Cerca nelle categorie
        matching_categories = categories.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )
        
        for cat in matching_categories:
            results.append({
                'type': 'category',
                'category_id': cat.id,
                'category_name': cat.name,
                'icon': cat.icon,
                'description': cat.description,
                'match_type': 'metadata',
                'owner': cat.owner.username if cat.owner else None
            })
        
        # Cerca nei file di contenuto
        for cat in categories:
            try:
                file_path = os.path.join(settings.PROCEDURE_FILES_DIR, cat.filename)
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Cerca nel contenuto
                    if query.lower() in content.lower():
                        # Trova le sezioni che contengono la query
                        sections = parse_procedure_file(content)
                        matching_sections = []
                        
                        for section in sections:
                            section_match = False
                            matching_commands = []
                            
                            # Cerca nel titolo e descrizione della sezione
                            if query.lower() in section['title'].lower() or query.lower() in section['desc'].lower():
                                section_match = True
                            
                            # Cerca nei comandi
                            for cmd in section['commands']:
                                if query.lower() in cmd['label'].lower() or query.lower() in cmd['cmd'].lower():
                                    matching_commands.append(cmd)
                            
                            if section_match or matching_commands:
                                matching_sections.append({
                                    'title': section['title'],
                                    'desc': section['desc'],
                                    'has_match': True,
                                    'matching_commands': len(matching_commands)
                                })
                        
                        if matching_sections:
                            results.append({
                                'type': 'content',
                                'category_id': cat.id,
                                'category_name': cat.name,
                                'icon': cat.icon,
                                'match_type': 'content',
                                'sections': matching_sections,
                                'owner': cat.owner.username if cat.owner else None
                            })
            
            except Exception as e:
                # Ignora errori di lettura file singoli
                continue
        
        return JsonResponse({
            'success': True,
            'query': query,
            'results': results,
            'total': len(results)
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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

@role_required('admin', 'editor')
def create_procedure_wysiwyg(request):
    """API per creare una nuova procedura usando l'editor WYSIWYG"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non consentito'}, status=405)
    
    try:
        # Ottieni i dati dal form
        name = request.POST.get('name', '').strip()
        icon = request.POST.get('icon', '📄')
        description = request.POST.get('description', '').strip()
        html_content = request.POST.get('content', '')
        is_public = request.POST.get('is_public', 'true').lower() == 'true'
        
        if not name or not html_content:
            return JsonResponse({'error': 'Nome e contenuto sono obbligatori'}, status=400)
        
        # Converti HTML in formato procedura .txt
        txt_content = convert_html_to_procedure_format(html_content)
        
        # Genera nome file unico
        base_filename = name.lower().replace(' ', '_')
        base_filename = ''.join(c for c in base_filename if c.isalnum() or c == '_')
        filename = f"{base_filename}.txt"
        
        # Gestisci duplicati
        counter = 1
        file_path = os.path.join(settings.PROCEDURE_FILES_DIR, filename)
        while os.path.exists(file_path):
            filename = f"{base_filename}_{counter}.txt"
            file_path = os.path.join(settings.PROCEDURE_FILES_DIR, filename)
            counter += 1
        
        # Salva il file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        
        # Crea la categoria nel database
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
            'message': 'Procedura creata con successo',
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
def update_procedure_wysiwyg(request, category_id):
    """API per aggiornare una procedura usando l'editor WYSIWYG"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non consentito'}, status=405)
    
    try:
        category = ProcedureCategory.objects.get(id=category_id)
        
        # Ottieni i dati
        html_content = request.POST.get('content', '')
        
        if not html_content:
            return JsonResponse({'error': 'Contenuto obbligatorio'}, status=400)
        
        # Converti HTML in formato procedura .txt
        txt_content = convert_html_to_procedure_format(html_content)
        
        # Sovrascrivi il file esistente
        file_path = os.path.join(settings.PROCEDURE_FILES_DIR, category.filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        
        return JsonResponse({
            'success': True,
            'message': 'Procedura aggiornata con successo'
        })
    
    except ProcedureCategory.DoesNotExist:
        return JsonResponse({'error': 'Categoria non trovata'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def convert_html_to_procedure_format(html_content):
    """Converte contenuto HTML dell'editor in formato procedura .txt"""
    from html.parser import HTMLParser
    
    class ProcedureHTMLParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.sections = []
            self.current_section = None
            self.current_command = None
            self.in_section_title = False
            self.in_section_desc = False
            self.in_command_label = False
            self.in_command_code = False
            self.text_buffer = []
        
        def handle_starttag(self, tag, attrs):
            attrs_dict = dict(attrs)
            
            if tag == 'h2':
                self.in_section_title = True
                if self.current_section:
                    self.sections.append(self.current_section)
                self.current_section = {'title': '', 'desc': '', 'commands': []}
            elif tag == 'p' and self.current_section and not self.current_section['desc']:
                self.in_section_desc = True
            elif tag == 'h3':
                self.in_command_label = True
                self.current_command = {'label': '', 'cmd': ''}
            elif tag == 'pre' or tag == 'code':
                self.in_command_code = True
        
        def handle_endtag(self, tag):
            if tag == 'h2':
                self.in_section_title = False
            elif tag == 'p':
                self.in_section_desc = False
            elif tag == 'h3':
                self.in_command_label = False
            elif tag == 'pre' or tag == 'code':
                self.in_command_code = False
                if self.current_command and self.current_section:
                    self.current_section['commands'].append(self.current_command)
                    self.current_command = None
        
        def handle_data(self, data):
            data = data.strip()
            if not data:
                return
            
            if self.in_section_title and self.current_section is not None:
                self.current_section['title'] += data
            elif self.in_section_desc and self.current_section is not None:
                self.current_section['desc'] += data
            elif self.in_command_label and self.current_command is not None:
                self.current_command['label'] += data
            elif self.in_command_code and self.current_command is not None:
                self.current_command['cmd'] += data
    
    parser = ProcedureHTMLParser()
    parser.feed(html_content)
    
    # Aggiungi l'ultima sezione
    if parser.current_section:
        parser.sections.append(parser.current_section)
    
    # Genera formato .txt
    txt_lines = []
    for section in parser.sections:
        txt_lines.append(f"[{section['title']}]")
        txt_lines.append(section['desc'])
        txt_lines.append('')
        
        for cmd in section['commands']:
            txt_lines.append(f"COMANDO: {cmd['label']}")
            txt_lines.append(cmd['cmd'])
            txt_lines.append('')
    
    return '\n'.join(txt_lines)

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
