# Generated by Django 4.2 on 2024-05-05 17:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservationhub', '0009_alter_gare_latitude_alter_gare_longitude'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gare',
            name='latitude',
            field=models.DecimalField(decimal_places=9, max_digits=20),
        ),
        migrations.AlterField(
            model_name='gare',
            name='longitude',
            field=models.DecimalField(decimal_places=9, max_digits=20),
        ),
    ]