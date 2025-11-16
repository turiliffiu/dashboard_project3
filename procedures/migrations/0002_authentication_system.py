# Generated migration for authentication system

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('procedures', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('admin', 'Amministratore'), ('editor', 'Editor'), ('viewer', 'Visualizzatore')], default='viewer', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Profilo Utente',
                'verbose_name_plural': 'Profili Utente',
            },
        ),
        migrations.AddField(
            model_name='procedurecategory',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='procedurecategory',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='procedures', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='procedurecategory',
            name='is_public',
            field=models.BooleanField(default=True, help_text='Se pubblico, tutti possono visualizzare'),
        ),
    ]
