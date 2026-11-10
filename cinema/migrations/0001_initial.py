# Generated manually for the initial CinemaHub domain models.

import django.core.validators
import django.db.models.deletion
from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Genre",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Hall",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Movie",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField()),
                ("duration", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(600)])),
                ("rating", models.DecimalField(decimal_places=1, max_digits=3, validators=[django.core.validators.MinValueValidator(Decimal("0.0")), django.core.validators.MaxValueValidator(Decimal("10.0"))])),
                ("age_rating", models.CharField(max_length=10)),
                ("genre", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="movies", to="cinema.genre")),
            ],
            options={"ordering": ["title"]},
        ),
        migrations.CreateModel(
            name="Seat",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("row", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("number", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("hall", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="seats", to="cinema.hall")),
            ],
            options={"ordering": ["hall_id", "row", "number"]},
        ),
        migrations.CreateModel(
            name="Session",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("start_time", models.DateTimeField()),
                ("price", models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(Decimal("0.01"))])),
                ("hall", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sessions", to="cinema.hall")),
                ("movie", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sessions", to="cinema.movie")),
            ],
            options={"ordering": ["start_time"]},
        ),
        migrations.AddConstraint(
            model_name="seat",
            constraint=models.UniqueConstraint(fields=("hall", "row", "number"), name="unique_seat_in_hall"),
        ),
    ]
