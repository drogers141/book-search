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
        parser.add_argument('-d', '--input-dir',
                            help='Specify the input directory.  This is recursive, files ending in .pdf or .epub ' +
                            'will be processed.')
        parser.add_argument('-f', '--file', help='Specify a single file to be processed.  Only one optional ' +
                            'parameter can be used.  If an input_dir and a file parameter are passed, only ' +
                            'the directory will be processed.')

    def handle(self, *args, **options):
        if options['input_dir']:
            for root, dirs, files in os.walk(options['input_dir']):
                logger.info('reading from input dir: %s', options['input_dir'])
                for infile in list(Path(root).glob('*.pdf')) + list(Path(root).glob('*.epub')):
                    self.convert_to_child_pages(infile)
        elif options['file']:
            self.convert_to_child_pages(Path(options['file']))

    def convert_to_child_pages(self, doc_file: Path):
        """Create parent, convert file to create children, save to db.

        This kicks off indexing into ES.
        .
        :param doc_file - input document
        """
        doc_path = doc_file.resolve()
        if not doc_path.is_file():
            logger.error('Cannot convert document, file does not exist: %s', doc_path)
            return
        parent_doc = ParentDocument(filepath=doc_path)
        parent_doc.save()
        try:
            parent_doc.convert_to_html_child_pages(doc_path)
            logger.info("Converted file: %s", doc_path)

        except IntegrityError as error:
            logger.error("%s, not inserting: %s", error, doc_path)

        except TikaParseError as error:
            logger.error('%s: failed to parse document: %s', error, doc_path)
            parent_doc.delete()



