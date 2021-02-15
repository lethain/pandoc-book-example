

# THIS REPOSITORY IS PROVIDED "AS IS" FOR FOLKS LOOKIN FOR A REAL EXAMPLE OF WORKING WITH PANDOC FOR A REAL BOOK. UNFORTUNATELY I WILL NOT BE ABLE TO ANSWER QUESTIONS ABOUT HOW TO USE ANY OF THESE PIECES, AND IT IS NOT MEANT TO BE USED DIRECTLY. IT IS INSTEAD INTENDED TO BE USED AS A REFERENCE FOR A FEW DIFFERENT IDEAS AND SO ON!


This repository contains the interesting pieces behind the build process used for _[Staff Engineer](https://staffeng.com)_.

---





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
