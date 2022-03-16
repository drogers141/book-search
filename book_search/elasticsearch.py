import re
from pprint import pprint

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

import logging

logger = logging.getLogger(__name__)

host = "127.0.0.1"
port = 9200
timeout = 1000

EDGE_STRIP_REGEX = re.compile(r'^>|<$|^[,.\-:;"”]+')


def clean_highlight(highlight_html: str):
    """Clean possible unwanted leading and trailing characters"""
    return re.sub(EDGE_STRIP_REGEX, '', highlight_html)


def move_single_inner_hit_up(query_return):
    """Moves a single nested inner hit to parent dict.

    This has to be done because template logic can't call
    {{ result['inner_hits'][0] }}.
    """
    for hit in query_return:
        if hit['num_inner_hits'] == 1:
            hit['single_inner_hit'] = hit['inner_hits'][0]
    return query_return


def add_highlight_count(query_return):
    # must be called before move_single_inner_hit_up
    for hit in query_return:
        for inner_hit in hit['inner_hits']:
            inner_hit['highlight_count'] = len(inner_hit['highlights'])
    # print('add_highlight_count:')
    # pprint(query_return)
    return query_return


def match_search(query: str) -> (int, list):
    client = Elasticsearch([{'host': host, 'port': port}], timeout=timeout)
    response = client.search(
        index = "booksearch",
        body = {
            "_source": [
                "author", "title", "course",
                "section", "module", "parent_doc_id",
                "page_number"
            ],
            "query": {
                "match": {
                    "content": {
                        # "query": f"{query}"
                        "query": "second wisdom"
                    }
                }
            },
            "collapse": {
                "field": "parent_doc_id",
                "inner_hits": {
                    "name": "matched_pages",
                    "size": 5,
                    "_source": [
                        "author", "title", "course",
                        "section", "module", "parent_doc_id",
                        "page_number"
                    ],
                    "highlight": {
                        "fields": {
                            "content": { "type": "plain" }
                        },
                        "fragment_size": "100"
                    }
                }
            }
        }

    )
    return_list = []
    total_hits = int(response['hits']['total']['value'])
    for hit in response['hits']['hits']:
        # print(f"hit:")
        # pprint(hit)
        hit_return = {
            'parent_doc_id': hit['_source']['parent_doc_id'],
            'title': hit['_source']['title'],
            'author': hit['_source']['author'],
            'course': hit['_source']['course'],
            'module': hit['_source']['module'],
            'section': hit['_source']['section'],
            'num_inner_hits': len(hit['inner_hits']['matched_pages']['hits']['hits']),
            'inner_hits': []
        }
        # print(f"inner_hits: {len(hit['inner_hits']['matched_pages']['hits']['hits'])}")
        for inner_hit in hit['inner_hits']['matched_pages']['hits']['hits']:
            # print('inner hit')
            hit_return['inner_hits'].append(
                {
                    'parent_doc_id': inner_hit['_source']['parent_doc_id'],
                    'title': inner_hit['_source']['title'],
                    'author': inner_hit['_source']['author'],
                    'page_number': inner_hit['_source']['page_number'],
                    'course': inner_hit['_source']['course'],
                    'module': inner_hit['_source']['module'],
                    'section': inner_hit['_source']['section'],
                    'highlights': [clean_highlight(highlight)
                                   for highlight in inner_hit['highlight']['content']]


                }
            )
        return_list.append(hit_return)
    return_list = add_highlight_count(return_list)
    return_list = move_single_inner_hit_up(return_list)
    return total_hits, return_list


def match_phrase_search(query: str) -> (int, list):
    client = Elasticsearch([{'host': host, 'port': port}], timeout=timeout)
    response = client.search(
        index = "booksearch",
        body = {
            "_source": [
                "author", "title", "course",
                "section", "module", "parent_doc_id",
                "page_number"
            ],
            "query": {
                "match_phrase": {
                    "content": {
                        # "query": f"{query}"
                        "query": query
                    }
                }
            },
            "collapse": {
                "field": "parent_doc_id",
                "inner_hits": {
                    "name": "matched_pages",
                    "size": 5,
                    "_source": [
                        "author", "title", "course",
                        "section", "module", "parent_doc_id",
                        "page_number"
                    ],
                    "highlight": {
                        "fields": {
                            "content": { "type": "plain" }
                        },
                        "fragment_size": "100"
                    }
                }
            }
        }

    )
    return_list = []
    total_hits = int(response['hits']['total']['value'])
    for hit in response['hits']['hits']:
        # print(f"hit:")
        # pprint(hit)
        hit_return = {
            'parent_doc_id': hit['_source']['parent_doc_id'],
            'title': hit['_source']['title'],
            'author': hit['_source']['author'],
            'course': hit['_source']['course'],
            'module': hit['_source']['module'],
            'section': hit['_source']['section'],
            'num_inner_hits': len(hit['inner_hits']['matched_pages']['hits']['hits']),
            'inner_hits': []
        }
        # print(f"inner_hits: {len(hit['inner_hits']['matched_pages']['hits']['hits'])}")
        for inner_hit in hit['inner_hits']['matched_pages']['hits']['hits']:
            # print('inner hit')
            hit_return['inner_hits'].append(
                {
                    'parent_doc_id': inner_hit['_source']['parent_doc_id'],
                    'title': inner_hit['_source']['title'],
                    'author': inner_hit['_source']['author'],
                    'page_number': inner_hit['_source']['page_number'],
                    'course': inner_hit['_source']['course'],
                    'module': inner_hit['_source']['module'],
                    'section': inner_hit['_source']['section'],
                    'highlights': [clean_highlight(highlight)
                                   for highlight in inner_hit['highlight']['content']]


                }
            )
        return_list.append(hit_return)
    return_list = add_highlight_count(return_list)
    return_list = move_single_inner_hit_up(return_list)
    return total_hits, return_list


QUOTE_QUERY_REGEX = re.compile(r"""["'](.*)["']""")


def handle_query(query: str) -> (int, list):
    """Dispatch to actual query function."""
    # match phrase on quotes - only whole expression quoted accepted at this point
    # ie query == "'three wisdoms'", not "word word 'quoted words'"
    # query_content = query['query']
    m = QUOTE_QUERY_REGEX.match(query)
    if m:
        match_query = m.groups()[0]
        logger.info(f"""query: %r running match_phrase search: '%s' """, query, match_query)
        return match_phrase_search(match_query)
    logger.info("""query: %r running plain match search: '%s' """, query, query)
    return match_search(query)




### Example of using ES dsl

# def esearch(firstname="", gender=""):
#     client = Elasticsearch()
#     q = Q("bool", should=[Q("match", firstname=firstname),
#                           Q("match", gender=gender)], minimum_should_match=1)
#     s = Search(using=client, index="bank").query(q)[0:20]
#     response = s.execute()
#     #print("%d hits found." % response.hits.total)
#     search = get_results(response)
#     return search

