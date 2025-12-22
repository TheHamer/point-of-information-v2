# Generated manually for adding tournament_url field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('speakstracker', '0009_speaks_call'),
    ]

    operations = [
        migrations.AddField(
            model_name='speaks',
            name='tournament_url',
            field=models.URLField(
                blank=True,
                help_text='URL of the competition homepage if imported from a link',
                max_length=500,
                null=True
            ),
        ),
    ]

