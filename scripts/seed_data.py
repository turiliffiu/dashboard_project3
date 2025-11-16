"""
Script per popolare il database con dati di esempio
Eseguire con: python manage.py shell < scripts/seed_data.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_mosaic.settings')
django.setup()

from django.contrib.auth.models import User
from skills.models import Skill, UserSkill, SkillCategory
from badges.models import Badge

print("🌱 Inizio seed database...")

# Crea categorie skill
categories_data = [
    {'name': 'Programmazione', 'icon': 'fa-code', 'color': '#3B82F6'},
    {'name': 'Design', 'icon': 'fa-palette', 'color': '#EC4899'},
    {'name': 'Marketing', 'icon': 'fa-bullhorn', 'color': '#10B981'},
    {'name': 'Management', 'icon': 'fa-briefcase', 'color': '#F59E0B'},
]

print("📊 Creazione categorie skill...")
for cat_data in categories_data:
    cat, created = SkillCategory.objects.get_or_create(
        name=cat_data['name'],
        defaults=cat_data
    )
    if created:
        print(f"  ✓ {cat.name}")

# Crea skill
skills_data = [
    ('Python', 'Programmazione'),
    ('JavaScript', 'Programmazione'),
    ('Django', 'Programmazione'),
    ('React', 'Programmazione'),
    ('UI/UX Design', 'Design'),
    ('Photoshop', 'Design'),
    ('SEO', 'Marketing'),
    ('Content Marketing', 'Marketing'),
    ('Project Management', 'Management'),
    ('Team Leadership', 'Management'),
]

print("🧠 Creazione competenze...")
for skill_name, cat_name in skills_data:
    category = SkillCategory.objects.get(name=cat_name)
    skill, created = Skill.objects.get_or_create(
        name=skill_name,
        defaults={'category': category, 'is_active': True}
    )
    if created:
        print(f"  ✓ {skill.name}")

# Crea badge
badges_data = [
    {
        'name': 'First Steps',
        'description': 'Completa il tuo profilo',
        'rarity': 'common',
        'points': 10,
    },
    {
        'name': 'Skill Master',
        'description': 'Aggiungi 10 competenze',
        'rarity': 'uncommon',
        'points': 50,
    },
]

print("🏆 Creazione badge...")
for badge_data in badges_data:
    # Nota: icon richiede un file, per ora lasciamo vuoto
    badge, created = Badge.objects.get_or_create(
        name=badge_data['name'],
        defaults={
            'description': badge_data['description'],
            'rarity': badge_data['rarity'],
            'points': badge_data['points'],
        }
    )
    if created:
        print(f"  ✓ {badge.name}")

print("✅ Seed completato!")
print("\n📝 Prossimi passi:")
print("1. Crea un superuser: python manage.py createsuperuser")
print("2. Accedi all'admin: http://localhost:8000/admin/")
