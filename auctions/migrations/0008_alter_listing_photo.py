# Generated by Django 3.2.7 on 2022-01-17 14:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0007_alter_listing_photo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listing',
            name='photo',
            field=models.ImageField(blank=True, default='images/20210527-baechu-kimchi-vicky-wasik-seriouseats-seriouseats-3-18a2d6d7d1d74a7a82c_4C1LTps.jpeg', null=True, upload_to='images/'),
        ),
    ]
