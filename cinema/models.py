from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Movie(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    genre = models.ForeignKey(Genre, on_delete=models.PROTECT, related_name="movies")
    duration = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(600)]
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(Decimal("0.0")), MaxValueValidator(Decimal("10.0"))],
    )
    age_rating = models.CharField(max_length=10)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Hall(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Seat(models.Model):
    hall = models.ForeignKey(Hall, on_delete=models.PROTECT, related_name="seats")
    row = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    number = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["hall", "row", "number"], name="unique_seat_in_hall"
            )
        ]
        ordering = ["hall_id", "row", "number"]

    def __str__(self):
        return f"{self.hall}: row {self.row}, seat {self.number}"


class Session(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.PROTECT, related_name="sessions")
    hall = models.ForeignKey(Hall, on_delete=models.PROTECT, related_name="sessions")
    start_time = models.DateTimeField()
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return f"{self.movie} at {self.start_time}"
