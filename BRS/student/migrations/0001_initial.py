# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-02-25 16:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ratings',
            fields=[
                ('cardnumber', models.CharField(max_length=14, primary_key=True, serialize=False)),
                ('barcode', models.CharField(max_length=9)),
                ('rating', models.IntegerField()),
            ],
            options={
                'db_table': 'ratings',
                'managed': False,
            },
        ),
    ]
