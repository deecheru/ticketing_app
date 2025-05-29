# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_alter_company_options_alter_profile_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='password_reset_token',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='password_reset_token_created',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ] 