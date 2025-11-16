from django.core.management.base import BaseCommand
from procedures.models import ProcedureCategory

class Command(BaseCommand):
    help = 'Popola il database con categorie di esempio'

    def handle(self, *args, **kwargs):
        categories = [
            {
                'name': 'Comandi Docker',
                'icon': '🐳',
                'description': 'Gestione container e immagini Docker',
                'filename': 'docker.txt',
                'order': 1
            },
            {
                'name': 'Comandi Linux',
                'icon': '🐧',
                'description': 'Comandi essenziali per amministrazione Linux',
                'filename': 'linux.txt',
                'order': 2
            },
            {
                'name': 'Comandi Git',
                'icon': '🔀',
                'description': 'Controllo versione e gestione repository',
                'filename': 'git.txt',
                'order': 3
            },
        ]

        for cat_data in categories:
            cat, created = ProcedureCategory.objects.get_or_create(
                filename=cat_data['filename'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Creato: {cat.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'- Già esistente: {cat.name}'))