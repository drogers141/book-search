from django.shortcuts import render

from .forms import SearchForm
from .elasticsearch import handle_query
from .models import ChildPage


def home(request):
    context = {}
    return render(request, 'book_search/home.html', context)


# todo should be GET
def search(request):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data
            total_hits, results = handle_query(query['query'])
            return render(request, "book_search/search.html",
                          {'form': form,
                           'total_hits': total_hits,
                           'results': results})

    else:
        form = SearchForm()

    return render(request, "book_search/search.html",
                  {'form': form,
                   'results': ''})

def view_page(request, document: int, page: int):
    child_page = ChildPage.objects.filter(parent_id=document).filter(page_number=page)[0]
    return render(request, "book_search/document_page.html",
                  {'html': child_page.html_content,
                   'page_number': child_page.page_number,
                   'title': child_page.title,
                   'author': child_page.author})

## query for parent_doc_id == 6 and page_number == 1
# In [5]: ChildPage.objects.filter(parent__id=6).filter(page_number=1)
# Out[5]: <QuerySet [<ChildPage: Cortland Dahl - The Three Wisdoms Exploring Reality M1 S1 - page 1>]>
