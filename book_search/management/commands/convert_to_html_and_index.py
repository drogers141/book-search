from pathlib import Path
import os
import logging

import yaml
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from book_search.models import ParentDocument


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """Convert each pair of input pdf and yaml metadata files into a lightweight parent
    object and a child object containing the html for each page."""

    def add_arguments(self, parser):
        parser.add_argument('input_dir',
                            help='Specify the input directory.  This is recursive, files ending in .pdf or .epub ' +
                            'will be processed.')

    def handle(self, *args, **options):
        # self.stdout.write(f"args: {args}, options: {options}")
        self.stdout.write(f"Reading from input dir: {options['input_dir']}")

        for root, dirs, files in os.walk(options['input_dir']):
            for infile in Path(root).glob('*.pdf') + Path(root).glob('*.epub'):
                try:
                    logger.info(f'processing {infile}')
                    self.convert_to_child_pages(infile)
                    # print(f"pdf: {pdf}  metadata: {metadata_file}")
                except IntegrityError as error:
                    logger.error("%s, not inserting: %s", error, infile)

    def convert_to_child_pages(self, doc_file: Path):
        """Create parent, convert file to create children, save to db.

        This kicks off indexing into ES.
        .
        :param doc_file - input document
        """
        self.stdout.write(f"doc_file: {doc_file.as_posix()}")
        parent_doc = ParentDocument(doc_file.as_posix())
        parent_doc.save()
        parent_doc.convert_to_html_child_pages(doc_file.as_posix())
        # logger.info("Converted file: %s", doc_file.as_posix())
        self.stdout.write(f"Converted file: {doc_file.as_posix()}")




