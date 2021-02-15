
Repository for building the _Staff Engineer_ book.

## Setup

Add some prerequisites:

    brew install pandoc

Checkout this repository and `lethain:staff-eng` as peer directories:

    cd ~/git
    git@github.com:lethain/book-staff-eng.git
    git@github.com:lethain/staff-eng.git

Then go into the `book-staff-eng` and initialize the Python dependencies:

    python3 -m venv ./env
    . ./env/bin/activate
    pip install -r requirements.txt


## Build the book

Simplest is to use make commands:

    make epub
    make pdf

Alternatively, you can generate "bound" book of markdown
that Pandoc can then convert into whatever:

    python gen.py index.yaml | pandoc -f markdown -t pdf

This can get very complex!

    python gen.py index.yaml | pandoc --toc --toc-depth=2 -V colorlinks -V link=blue -f markdown -t pdf  > book.pdf


That's simpler, but obviously LaTeX gives a bunch of great tools like
e.g. chapters and so on for free.


## Build epub

Build step:

    python gen.py index.yaml | pandoc --toc --toc-depth=2 -V colorlinks -V link=blue -f markdown -o book.epub

Very helpful tutorial [on this medium post](https://medium.com/programmers-developers/building-books-with-markdown-using-pandoc-f0d19df7b2ca)
including how to add a cover later on!


## More resources

* https://pandoc.org/MANUAL.html#extension-yaml_metadata_block
* https://learnbyexample.github.io/customizing-pandoc/
* https://pandoc.org/MANUAL.html#general-options
