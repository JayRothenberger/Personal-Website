# Generated by Django 3.0.2 on 2020-07-12 17:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('personal', '0004_apikey'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='choice',
            name='question',
        ),
        migrations.DeleteModel(
            name='Suggestion',
        ),
        migrations.DeleteModel(
            name='Choice',
        ),
        migrations.DeleteModel(
            name='Question',
        ),
    ]
