# Generated by Django 3.2.10 on 2022-01-02 19:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('host', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='host',
            name='name',
            field=models.CharField(max_length=100, primary_key=True, serialize=False),
        ),
    ]
