"""Elasticsearch document model for django-elasticsearch-dsl
"""
from elasticsearch_dsl import analyzer
from django_elasticsearch_dsl import Document, fields, Keyword
from django_elasticsearch_dsl.registries import registry
from .models import ChildPage


booksearch_analyzer = analyzer(
    "booksearch_analyzer",
    tokenizer="standard",
    filter=['lowercase', 'asciifolding', 'porter_stem'],
    char_filter=['html_strip']
)


@registry.register_document
class ChildPageDocument(Document):

    content = fields.TextField(attr='html_content',
                               analyzer=booksearch_analyzer)
    title = fields.TextField(fields={'keyword': Keyword()})
    author = fields.KeywordField(attr='author')

    class Index:
        name = 'booksearch'
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 1}

    class Django:
        model = ChildPage
        fields = [
            'page_number',
            'parent_doc_id'
        ]

        # Ignore auto updating of Elasticsearch when a model is saved
        # or deleted:
        # ignore_signals = True

        # Don't perform an index refresh after every update (overrides global setting):
        # auto_refresh = False

        # Paginate the django queryset used to populate the index with the specified size
        # (by default it uses the database driver's default setting)
        # queryset_pagination = 5000
