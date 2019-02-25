# Generated by Django 2.1.3 on 2019-02-24 15:23

from django.db import migrations, models
import systems.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_auto_20190223_0847'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='config',
            field=systems.models.fields.EncryptedDataField(default={}),
        ),
        migrations.AddField(
            model_name='user',
            name='state_config',
            field=systems.models.fields.EncryptedDataField(default={}),
        ),
        migrations.AddField(
            model_name='user',
            name='type',
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='variables',
            field=systems.models.fields.EncryptedDataField(default={}),
        ),
        migrations.AlterField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(related_name='_user_groups_+', to='group.Group'),
        ),
    ]
