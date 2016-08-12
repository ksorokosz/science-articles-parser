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
# - datefinder

import sys, time, codecs
import io, os, re

default_encoding = 'cp1250' # PDF file meta data default encoding (maybe platform dependent)
sys.stdout = codecs.getwriter('utf8')(sys.stdout)
sys.stderr = codecs.getwriter('utf8')(sys.stderr)

import datefinder
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure

# Extract date from pdf file - heuristic
def get_date(pdfdata):

	text = parse_layout(pdfdata)
	pdflines = iter(text.splitlines())
	date = []
	for line in pdflines:
		try:
			extracted = list(datefinder.find_dates(line))
		except:
			continue
		if extracted:
			date.extend(extracted)
			
	return date

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
			break
		if parsing:
			index = line.lower().find("abstract")
			if index != -1:
				line = line[index+len("abstract"):] # Remove abstract word
			abstract = ''.join([abstract, line])
			
	# Remove non-ascii
	abstract = ''.join(c if ord(c) < 129 and ord(c) > 0 else '' for c in abstract)
	
	# Fix whitespaces
	abstract = ' '.join(abstract.split()).replace("\n",' ').strip()
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
def convert_article(path):

	rsrcmgr = PDFResourceManager()
	laparams = LAParams()
	device = PDFPageAggregator(rsrcmgr, laparams=laparams)

	fp = file(path, 'rb')
	parser = PDFParser(fp)
	doc = PDFDocument(parser)
	parser.set_document(doc)

	interpreter = PDFPageInterpreter(rsrcmgr, device)
	maxpages = 0
	caching = True
	pagenos=set()
	
	metadata = { 'Title': '' , 'Author': '', 'Abstract': '' }
	
	# Get title and author from pdf metadata
	for meta in doc.info:
		try:
			title = ''.join(c if ord(c) < 129 and ord(c) > 0 else '' for c in meta['Title']) # Only ASCII characters
			author = ''.join(c if ord(c) < 129 and ord(c) > 0 else '' for c in meta['Author']) # Only ASCII characters
			title = title.decode(default_encoding)
			author = author.decode(default_encoding)
			metadata = { "Title": title, "Author": author, "Abstract": '', "Date": '' }
		except:
			continue
			
	# Parse pdf file
	date = []
	for index, page in enumerate(PDFPage.get_pages(fp, pagenos, maxpages=maxpages, 
				  caching=caching,check_extractable=True)):
		interpreter.process_page(page)
		pdfdata = device.get_result()
		date.extend(get_date(pdfdata))

		# Abstract should be published on first page
		if index == 0:
			abstract = get_abstract(pdfdata)
			metadata["Abstract"] = abstract	

	metadata["Date"] = date[0].year # First detected date
		
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
		print "%s\t%s\t%s\t%s\t%s" % \
		( pdffile, retrieved_info['Title'], retrieved_info['Author'], 
		  retrieved_info['Date'], retrieved_info['Abstract'])

if __name__ == "__main__":
	parse_articles()