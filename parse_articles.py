# Python 2.7 compatible (tested on windows)
#
# Script read list of files from stdin (format: label <tab> path )
# and prints summary about science articles on stdout ( format: title <tab> author <tab> abstract)
#
# Script may help to organize science articles and summarize them.
#
# Note: script removes non-ascii data, multiple whitespaces, new lines etc.
# Note: script analyze pdf metadata to get authors and title. Abstract is retrieved from pdf file itself
# Note: script is simple but it will be extended in the future
# 
# Dependencies:
# - pdfminer

import sys, time, codecs
import io, os, re

default_encoding = 'cp1250' # PDF file meta data default encoding (maybe platform dependent)
sys.stdout = codecs.getwriter('utf8')(sys.stdout)
sys.stderr = codecs.getwriter('utf8')(sys.stderr)

from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure

# Extract abstract from pdf file - heuristic
def get_abstract(pdfdata):

	text = parse_layout(pdfdata)
	pdflines = iter(text.splitlines())
	parsing = False
	abstract = ''
	for line in pdflines:
		if "abstract" in line.lower(): # From abstract
			parsing = True
		elif not line.strip() and abstract: # Until empty line and abstract is readed
			parsing = False
		if parsing:
			index = line.lower().find("abstract")
			if index != -1:
				line = line[index+len("abstract")+1:] # Remove abstract
			abstract = ''.join([abstract, line])
			
	abstract = ''.join(c if ord(c) < 129 and ord(c) > 0 else '' for c in abstract)
	abstract = ' '.join(abstract.split())
	return abstract
		

# Parse layout - for now simply get text (consider to classify text in the future)
def parse_layout(pdfdata):
	text = ''
	for lt_obj in pdfdata:
		if isinstance(lt_obj, LTTextBox) or isinstance(lt_obj, LTTextLine):
			text = '\n'.join([text, lt_obj.get_text()])
	return text
			
# Convert PDF
# http://stackoverflow.com/questions/5725278/how-do-i-use-pdfminer-as-a-library
# https://github.com/timClicks/slate/issues/5
def convert_article(path):

	rsrcmgr = PDFResourceManager()
	laparams = LAParams()
	device = PDFPageAggregator(rsrcmgr, laparams=laparams)

	fp = file(path, 'rb')
	parser = PDFParser(fp)
	doc = PDFDocument(parser)
	parser.set_document(doc)

	interpreter = PDFPageInterpreter(rsrcmgr, device)
	maxpages = 1
	caching = True
	pagenos=set()
	
	metadata = {}
	
	# Get title and author from pdf metadata
	for meta in doc.info:
		title = meta['Title'].decode(default_encoding)
		author = meta['Author'].decode(default_encoding)
		title = ''.join(c if ord(c) < 129 and ord(c) > 0 else '' for c in title) # Only ASCII characters
		author = ''.join(c if ord(c) < 129 and ord(c) > 0 else '' for c in author) # Only ASCII characters
		metadata = { "Title": title, "Author": author, "Abstract": '' }
	
	# Get abstract from file
	for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, 
				  caching=caching,check_extractable=True):
		interpreter.process_page(page)
		pdfdata = device.get_result()
		abstract = get_abstract(pdfdata).replace("\n",' ').strip()
		metadata["Abstract"] = abstract
		
	fp.close()
	device.close()
	return metadata

# Parse science articles
def parse_articles():
	
	# For each pdf file
	for line in sys.stdin:
		
		line = line.strip()
		(name, pdffile) = line.split("\t"); # name for validation
		
		retrieved_info = convert_article( pdffile )
		print "%s\t%s\t%s" % ( retrieved_info['Title'], retrieved_info['Author'], retrieved_info['Abstract'])

if __name__ == "__main__":
	parse_articles()