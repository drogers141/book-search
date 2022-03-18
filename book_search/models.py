from io import StringIO
import re
from pathlib import Path

from tika import parser
from django.db import models
from bs4 import BeautifulSoup


def extract_author_and_title(metadata):
    pass


class ParentDocument(models.Model):
    """Each book/file is represented here.
    """
    # source document's full path
    filepath = models.CharField(max_length=1024)

    # try to get the author and title from the document metadata
    # but it's not always there
    author = models.CharField(max_length=512, blank=True, default='')
    title = models.CharField(max_length=512, blank=True, default='')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['filepath',],
                name='filepath')
        ]

    def __str__(self):
        return f"id: {self.id}  {self.author} - {self.title}"

    def convert_to_html_child_pages(self, filepath: str, clean=True):
        """Convert filepath (pdf at this point) to html pages.

        This constructs a ChildPage object for each page of the document.
        Pages are determined by Tika's parsing.

        Populates author and title if available in the metadata.

        :param filepath - path to input [pdf] file
        :param clean - if True clean non-ascii whitespace
        """
        data = parser.from_file(filepath, xmlContent=True)
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

        self.filename = Path(filepath).name


class ChildPage(models.Model):
    """Each page of a book/file is represented by a ChildPage.

    If you want the implementation to support browsing books as html files,
    populate the html_content field.  If you want to save space, leave it empty.
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
