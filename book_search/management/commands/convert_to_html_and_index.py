from pathlib import Path
import os
import logging

import yaml
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from book_search.models import ParentDocument, TikaParseError


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """Convert each document file into a parent object containing the metadata and 
    and children such that each child object contains the html for each page."""

    def add_arguments(self, parser):
        parser.add_argument('input_dir',
                            help='Specify the input directory.  This is recursive, files ending in .pdf or .epub ' +
                            'will be processed.')

    def handle(self, *args, **options):
        # self.stdout.write(f"args: {args}, options: {options}")
        self.stdout.write(f"Reading from input dir: {options['input_dir']}")

        for root, dirs, files in os.walk(options['input_dir']):
            for infile in list(Path(root).glob('*.pdf')) + list(Path(root).glob('*.epub')):
                logger.info(f'processing {infile}')
                self.convert_to_child_pages(infile)

    def convert_to_child_pages(self, doc_file: Path):
        """Create parent, convert file to create children, save to db.

        This kicks off indexing into ES.
        .
        :param doc_file - input document
        """
        doc_path = doc_file.resolve()
        self.stdout.write(f"doc_file: {doc_path}")
        if not doc_path.is_file():
            logger.error('Cannot convert document, file does not exist: %s', doc_path)
            return
        parent_doc = ParentDocument(filepath=doc_path)
        parent_doc.save()
        try:
            parent_doc.convert_to_html_child_pages(doc_path)
            logger.info("Converted file: %s", doc_path)
            # self.stdout.write(f"Converted file: {doc_path}")
        except IntegrityError as error:
            logger.error("%s, not inserting: %s", error, doc_path)

        except TikaParseError as error:
            logger.error('%s: failed to parse document: %s', error, doc_path)
            parent_doc.delete()



