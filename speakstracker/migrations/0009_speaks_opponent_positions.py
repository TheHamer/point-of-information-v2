# Generated manually for adding opponent_positions field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('speakstracker', '0008_auto_20230313_1733'),
    ]

    operations = [
        migrations.AddField(
            model_name='speaks',
            name='opponent_positions',
            field=models.TextField(
                blank=True, 
                help_text='JSON list of opponent team positions', 
                null=True
            ),
        ),
    ]

