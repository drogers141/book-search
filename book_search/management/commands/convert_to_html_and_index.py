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
                            help='Specify the input directory.  The directory must contain pdf ' +
                            'files and yaml metadata files.  They must follow the naming ' +
                            'convention that for each pdf there is a corresponding file with the ' +
                            'same name but a .yml extension.  The yaml file has the metadata for ' +
                            'the pdf.  This is recursive, files that are not matching .pdf, .yml ' +
                            'pairs are ignored.')

    def handle(self, *args, **options):
        # self.stdout.write(f"args: {args}, options: {options}")
        self.stdout.write(f"Reading from input dir: {options['input_dir']}")

        for root, dirs, files in os.walk(options['input_dir']):
            for pdf in Path(root).glob('*.pdf'):
                metadata_file = f"{pdf.parent.as_posix()}/{pdf.stem}.yml"
                assert pdf.is_file() and Path(metadata_file).is_file(), 'pdf and metadata files?'
                try:
                    self.convert_to_child_pages(pdf, Path(metadata_file))
                    # print(f"pdf: {pdf}  metadata: {metadata_file}")
                except IntegrityError as error:
                    logger.error("Duplicate found, not inserting: %s", error)

    def convert_to_child_pages(self, doc_file: Path, meta_file: Path):
        """Create parent, convert file to create children, save to db.

        This kicks off indexing into ES.
        .
        :param doc_file - input document [pdf]
        :param meta_file- yaml file with metadata
        """
        self.stdout.write(f"pdf: {doc_file.as_posix()}  yaml: {meta_file.as_posix()}")
        metadata = yaml.safe_load(open(meta_file))
        parent_doc = ParentDocument(**metadata)
        parent_doc.save()
        parent_doc.convert_to_html_child_pages(doc_file.as_posix())
        # logger.info("Converted file: %s", doc_file.as_posix())
        self.stdout.write(f"Converted file: {doc_file.as_posix()}")




