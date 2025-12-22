# Generated manually for adding call field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('speakstracker', '0008_auto_20230313_1733'),
    ]

    operations = [
        migrations.AddField(
            model_name='speaks',
            name='call',
            field=models.TextField(
                blank=True, 
                help_text='JSON list of all 4 teams in rank order (1st to 4th)', 
                null=True
            ),
        ),
    ]

