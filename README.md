# Book Search
Basic full-text search engine for locally stored books or other files in pdf or epub.  Uses elasticsearch
postgresql, python and django, and Apache Tika.

## Work in progress

Looks like elasticsearch needs to be run without tls to allow http (not https) connections from
django-elasticsearch-dsl.  Need to look into configuring d-e-dsl for tls.

```
./elasticsearch -E xpack.security.enabled=false
```
