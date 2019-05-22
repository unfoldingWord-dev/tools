# How to use

Commands to install and use the script in `tools/bible/generate_bible_pdf`:

- [ ] Make sure Python 2.7 is installed
- [ ] Make sure wkhtmltopdf command line tool v0.12.6-dev (or higher) is installed (https://builds.wkhtmltopdf.org/0.12.6-dev for dev, https://wkhtmltopdf.org/downloads.html for other downloads)
- [ ] Install python requirements: `sudo pip install -r requirements`
- [ ] Make your working and output dirs: e.g. `mkdir ~/working`, `mkdir ~/output`
- [ ] To generate each individual book's PDF: `./run.sh -w ~/working -o ~/output -r ult`
- [ ] To generate one PDF of the whole NT: `./run.sh -w ~/working -o ~/output -r ust -b nt`
- [ ] `-r` for the resource (`ult` or `ulb`) and `-b` to specify the book (e.g. `mat`, `2pe`) or the New Testament (`nt`)
- [ ] Find your PDFs in `~/output/en_<resource>_pdf` (HTML also available in `en_<resource>_html`)
