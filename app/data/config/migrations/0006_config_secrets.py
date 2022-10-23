# Generated by Django 4.1.2 on 2022-10-22 23:38

from django.db import migrations
import systems.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('config', '0005_alter_config_config_alter_config_groups_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='config',
            name='secrets',
            field=systems.models.fields.EncryptedDataField(default={}, editable=False),
        ),
    ]
