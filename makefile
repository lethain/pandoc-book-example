
epub:
	python gen.py index.yaml | pandoc --epub-embed-font='fonts/*.ttf' --toc --toc-depth=2 -V colorlinks -V link=blue -f markdown -o book.epub

pdf:
	python gen.py index.yaml | \
	pandoc --template latex.template --toc --toc-depth=2 -V colorlinks -V link=blue \
	-V geometry:a5paper \
	-V geometry:margin=2cm \
	-H header.tex \
	--pdf-engine=xelatex \
	-f markdown -o book-interim.pdf && \
        ./cpdf StaffEngCover.pdf book-interim.pdf -o book.pdf

note:
	pandoc note.md \
	-V geometry:a5paper \
        -V geometry:margin=2cm \
	--pdf-engine=xelatex \
	-f markdown -o note.pdf \
	&& \
	./cpdf StaffEngCover.pdf note.pdf book-interim.pdf -o signed_book.pdf


print:
	python gen.py --print index.yaml | \
	pandoc --template print.template --toc --toc-depth=2 -V colorlinks -V link=blue \
	-V geometry:a5paper \
	-V geometry:margin=2cm \
	-H header.tex \
	--pdf-engine=xelatex \
	-f markdown \
	-o print_book.pdf

print_chapter_refs:
	python gen.py --print --chapter-refs index.yaml | \
	pandoc --template print.template --toc --toc-depth=2 -V colorlinks -V link=blue \
	-V geometry:a5paper \
	-V geometry:margin=2cm \
	-H header.tex \
	--pdf-engine=xelatex \
	-f markdown \
	-o interim_chapter_book.pdf \
	&& \
	./cpdf StaffEngCover.pdf interim_chapter_book.pdf -o print_chapter_book.pdf

latex:
	python gen.py --latex index.yaml > book.tex
