# Generated by Django 4.1.2 on 2022-10-26 07:15

from django.db import migrations
import systems.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('log', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='log',
            name='secrets',
            field=systems.models.fields.EncryptedDataField(default={}),
        ),
    ]
