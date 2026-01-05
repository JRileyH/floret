from datetime import datetime
from uuid import uuid4

from django.contrib import admin
from django.db import models
from django.db.models.query import QuerySet
from django.utils import timezone


class BaseQuerySet(QuerySet):
    def delete(self, now: datetime | None = None, hard: bool = False):
        if hard:
            return super().delete()
        if not now:
            now = timezone.now()
        return super().update(deleted_at=now)


class BaseManager(models.Manager):
    def __init__(self, *args, **kwargs) -> None:
        self.include_deleted = kwargs.pop("include_deleted", False)
        super().__init__(*args, **kwargs)

    def get_queryset(self) -> BaseQuerySet:
        if self.include_deleted:
            return BaseQuerySet(model=self.model)
        return BaseQuerySet(model=self.model).filter(deleted_at__isnull=True)

    def delete(self, now=None, hard=False):
        return self.get_queryset().delete(now, hard)


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False, blank=True)
    updated_at = models.DateTimeField(default=timezone.now, editable=True, blank=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = BaseManager(include_deleted=False)
    all_objects = BaseManager(include_deleted=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        return super().save(*args, **kwargs)

    def delete(self, now: datetime | None = None, hard: bool = False):
        if hard:
            return super().delete()
        if not now:
            now = timezone.now()
        self.deleted_at = now
        self.save(update_fields=["deleted_at", "updated_at"])
        return (1, {self._meta.label: 1})


class BaseModelAdmin(admin.ModelAdmin):
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "deleted_at",
    )

    class Meta:
        abstract = True


class BaseTabularInline(admin.TabularInline):
    readonly_fields = (
        "created_at",
        "updated_at",
        "deleted_at",
    )

    class Meta:
        abstract = True


class BaseStackedInline(admin.StackedInline):
    readonly_fields = (
        "created_at",
        "updated_at",
        "deleted_at",
    )

    class Meta:
        abstract = True
