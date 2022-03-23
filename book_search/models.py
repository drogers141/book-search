from io import StringIO
import re
from pathlib import Path
import logging

from django.db import models
from django.conf import settings
from bs4 import BeautifulSoup
from tika import parser

logger = logging.getLogger(__name__)


class TikaParseError(RuntimeError):
    """Raised when the conversion of a document into html by Tika fails."""


def extract_author_and_title(metadata: dict) -> (str, str):
    """Try to get the author and title from the metadata.
    Return empty strings if not found."""
    author, title = '', ''
    for key in ('Author', 'author', 'dc:creator', 'creator', 'meta:author'):
        if key in metadata:
            author = metadata[key]
            break
    for key in ('Title', 'title', 'dc:title', 'meta:title'):
        if key in metadata:
            title = metadata[key]
            break
    return author, title


class ParentDocument(models.Model):
    """Each book/file is represented here.
    """
    # source document's full path
    filepath = models.CharField(unique=True, max_length=1024)

    # try to get the author and title from the document metadata
    # but it's not always there
    author = models.CharField(max_length=512, blank=True, default='')
    title = models.CharField(max_length=512, blank=True, default='')

    def __str__(self):
        return f"id: {self.id}  {Path(self.filepath).name}"

    def convert_to_html_child_pages(self, clean=True):
        """Convert book/file at filepath to html pages.

        This constructs a ChildPage object for each page of the document.
        Pages are determined by Tika's parsing.

        Populates author and title if available in the metadata.

        :param clean - if True clean non-ascii whitespace
        """
        try_count, successful_parse = 0, False
        while try_count < settings.TIKA_PARSE_MAX_RETRY:
            if settings.TIKA_CONFIG_FILE:
                data = parser.from_file(str(self.filepath), xmlContent=True, config_path=settings.TIKA_CONFIG_FILE)
            else:
                data = parser.from_file(str(self.filepath), xmlContent=True)
            if data['status'] == 200:
                successful_parse = True
                break
        if not successful_parse:
            logger.error('Failed to parse file: %s', self.filepath)
        author, title = extract_author_and_title(data['metadata'])
        self.author, self.title = author, title
        self.save()
        soup = BeautifulSoup(data['content'], features='lxml')
        # convert all pages successfully before creating children
        pages = []

        for i, content in enumerate(soup.find_all('div', attrs={'class': 'page'})):
            _buffer = StringIO()
            _buffer.write(str(content))
            parsed_content = parser.from_buffer(_buffer.getvalue(), xmlContent=True)

            text = parsed_content['content'].strip()
            if clean:
                text = re.sub(r' +\n', '\n', parsed_content['content'].strip().replace('\xa0', ' '))

            # remove the html head from the doc so it doesn't cause any garbage in ES highlights
            page_soup = BeautifulSoup(text, features='lxml')
            page_soup.head.extract()
            pages.append(page_soup.prettify())

        for i, html in enumerate(pages):
            child = ChildPage(parent=self, page_number=i+1, html_content=html,
                              author=self.author, title=self.title,
                              parent_doc_id=self.id)
            if i == len(pages) - 1:
                child.is_last_page = True
            child.save()


class ChildPage(models.Model):
    """Each page of a book/file is represented by a ChildPage.

    With the initial implementation, this model will also have the html_content
    field filled with the full text of the page.  This is very inefficient
    space-wise as you are storing the full text in the database as well as in
    Elasticsearch.  But it allows reading the text online and being able to
    navigate directly from the search to the location in the text.

    The reason that it is mandatory now is due to using django-elasticsearch-dsl.
    In the future, we can get rid of django-es-dsl and then allow an option to
    not store the full text to save space.
    """

    parent = models.ForeignKey(ParentDocument, on_delete=models.CASCADE)
    page_number = models.IntegerField()
    html_content = models.TextField()
    is_last_page = models.BooleanField(default=False)

    # need to duplicate keys from parent so django-elasticsearch-dsl can access them
    author = models.CharField(max_length=512)
    title = models.CharField(max_length=512)

    parent_doc_id = models.IntegerField()

    def url(self):
        return f"/{self.parent_doc_id}/{self.page_number}/"

    def __str__(self):
        return (f"{self.author} - {self.title} - page {self.page_number}")
