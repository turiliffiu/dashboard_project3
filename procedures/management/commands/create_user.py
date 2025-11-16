from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from procedures.models import UserProfile


class Command(BaseCommand):
    help = 'Crea un nuovo utente con un ruolo specifico'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username dell\'utente')
        parser.add_argument('--email', type=str, help='Email dell\'utente', default='')
        parser.add_argument('--password', type=str, help='Password dell\'utente', default='password123')
        parser.add_argument('--role', type=str, choices=['admin', 'editor', 'viewer'], 
                          help='Ruolo dell\'utente', default='viewer')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        role = options['role']

        # Verifica se l'utente esiste già
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'Utente "{username}" esiste già'))
            return

        # Crea l'utente
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # Crea o aggiorna il profilo
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.role = role
        profile.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Utente "{username}" creato con successo!\n'
                f'  Ruolo: {profile.get_role_display()}\n'
                f'  Password: {password}\n'
            )
        )
