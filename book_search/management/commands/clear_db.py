from textwrap import dedent
from pathlib import Path
import logging

from django.core.management.base import BaseCommand
from django.utils import timezone, dateparse
from django.db import DatabaseError

from tergar_search.models import ParentDocument, ChildPage


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """Convenience command for deleting all ParentDocuments and ChildPages"""

    def handle(self, *args, **options):
        choice = input('Are you sure you want to delete all ParentDocuments and ChildPages? [Yy] ')
        if choice in ('Y', 'y'):
            ChildPage.objects.all().delete()
            ParentDocument.objects.all().delete()
            self.stdout.write('Removed all ChildPage and ParentDocument objects from db.')
        else:
            self.stdout.write('Not deleting.')
