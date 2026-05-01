from django.core.validators import MinValueValidator
from django.db import models
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit
from slugify import slugify


class Category(models.Model):
    name = models.CharField("Название", max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    order = models.PositiveIntegerField("Порядок", default=0, db_index=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Item(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Категория",
    )
    name = models.CharField("Название", max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField("Описание", blank=True)
    price = models.DecimalField(
        "Цена",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    image = models.ImageField(
        "Изображение",
        upload_to="menu/items/",
        blank=True,
        null=True,
    )
    thumb_300 = ImageSpecField(
        source="image",
        processors=[ResizeToFit(300, 300)],
        format="JPEG",
        options={"quality": 85},
    )
    is_new = models.BooleanField("Новинка", default=False)
    is_seasonal = models.BooleanField("Сезонное", default=False)
    is_active = models.BooleanField(default=True, db_index=True)
    order = models.PositiveIntegerField("Порядок", default=0, db_index=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Позиция меню"
        verbose_name_plural = "Позиции меню"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class RoastedCoffee(models.Model):
    name = models.CharField("Название", max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    origin = models.CharField("Страна", max_length=200, blank=True)
    region = models.CharField("Регион", max_length=200, blank=True)
    weight = models.CharField("Вес", max_length=50, blank=True, help_text="Например: 250g")
    flavor_notes = models.TextField("Букет вкуса", blank=True)
    brew_method = models.CharField("Способ приготовления", max_length=200, blank=True)
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    image = models.ImageField("Изображение", upload_to="roasted/", blank=True, null=True)
    thumb_300 = ImageSpecField(
        source="image",
        processors=[ResizeToFit(300, 300)],
        format="JPEG",
        options={"quality": 85},
    )
    is_active = models.BooleanField("Активно", default=True)
    order = models.PositiveIntegerField("Порядок", default=0, db_index=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Обжаренный кофе"
        verbose_name_plural = "Обжаренный кофе"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
