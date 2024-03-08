# Generated by Django 4.1.13 on 2024-03-08 08:24

from django.db import migrations, models
import django_celery_beat.validators


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0004_alter_scheduledtask_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taskcrontab',
            name='day_of_week',
            field=models.CharField(default='*', help_text='Cron Days Of The Week to Run. Use "*" for "all", Sunday is 0 or 7, Monday is 1. (Example: "0,5")', max_length=64, validators=[django_celery_beat.validators.day_of_week_validator], verbose_name='Day(s) Of The Week'),
        ),
        migrations.AlterField(
            model_name='taskcrontab',
            name='month_of_year',
            field=models.CharField(default='*', help_text='Cron Months (1-12) Of The Year to Run. Use "*" for "all". (Example: "1,12")', max_length=64, validators=[django_celery_beat.validators.month_of_year_validator], verbose_name='Month(s) Of The Year'),
        ),
    ]
