# Book Search
Basic full-text search engine for locally stored books or other files in pdf or epub.  Uses elasticsearch
postgresql, python and django, and Apache Tika.

## Notes
Using python-tika which downloads a Tika jar and then runs it as a server.  This is all fine except if you
have Tesseract OCR installed and want decent performance.  I'm assuming that pdfs and epubs for this search
engine are not needing to be OCR'd, but rather have text streams available.  This is for performance and 
quality of search.  ocrmypdf or a similar tool can be used to populate the text stream.  So given that, the 
problem is that if Tesseract is installed, Tika will enable it and 
parsing a book can take 90 seconds rather than 2.  



