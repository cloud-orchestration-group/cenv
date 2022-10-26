# Generated by Django 4.1.2 on 2022-10-25 20:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0007_alter_scheduledtask_options_remove_scheduledtask_id_and_more'),
        ('user', '0006_user_secrets'),
        ('log', '0005_remove_log_scheduled_log_schedule_log_worker'),
    ]

    operations = [
        migrations.AlterField(
            model_name='log',
            name='schedule',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(data_name)s', to='schedule.scheduledtask'),
        ),
        migrations.AlterField(
            model_name='log',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(data_name)s', to='user.user'),
        ),
    ]
