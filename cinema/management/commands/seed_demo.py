from decimal import Decimal

from django.core.management.base import BaseCommand

from cinema.models import Genre, Movie


DEMO_MOVIES = [
    {
        "genre": "Наукова фантастика",
        "title": "Interstellar",
        "description": "Експедиція крізь космос у пошуках нового дому для людства.",
        "duration": 169,
        "rating": Decimal("8.7"),
        "age_rating": "12+",
    },
    {
        "genre": "Драма",
        "title": "The Shawshank Redemption",
        "description": "Історія дружби та надії у в'язниці Шоушенк.",
        "duration": 142,
        "rating": Decimal("9.3"),
        "age_rating": "16+",
    },
    {
        "genre": "Пригоди",
        "title": "The Lord of the Rings: The Fellowship of the Ring",
        "description": "Фродо вирушає в небезпечну подорож до Мордору.",
        "duration": 178,
        "rating": Decimal("8.8"),
        "age_rating": "12+",
    },
    {
        "genre": "Комедія",
        "title": "The Grand Budapest Hotel",
        "description": "Пригоди консьєржа легендарного готелю та його учня.",
        "duration": 99,
        "rating": Decimal("8.1"),
        "age_rating": "12+",
    },
    {
        "genre": "Анімація",
        "title": "Spider-Man: Into the Spider-Verse",
        "description": "Майлз Моралес відкриває світ альтернативних Людей-павуків.",
        "duration": 117,
        "rating": Decimal("8.4"),
        "age_rating": "6+",
    },
]


class Command(BaseCommand):
    help = "Create or update five CinemaHub demonstration movies."

    def handle(self, *args, **options):
        for item in DEMO_MOVIES:
            genre, _ = Genre.objects.get_or_create(name=item["genre"])
            movie_data = {key: value for key, value in item.items() if key != "genre"}
            Movie.objects.update_or_create(title=item["title"], defaults={**movie_data, "genre": genre})
        self.stdout.write(self.style.SUCCESS("Demo movies are ready."))
