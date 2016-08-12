# Python 2.7 compatible (tested on windows)
#
# Script read list of files from stdin (format: label <tab> path )
# and rename them according to format AUTHOR_TITLE_DATE
#
# Script may help to organize science articles and summarize them.
#
# Note: script removes non-ascii data, multiple whitespaces, new lines etc.
# Note: script analyze pdf metadata to get authors and title. Date is retrieved from pdf file itself
# Note: script is simple but it will be extended in the future
# 
# Dependencies:
# - pdfminer

import sys, time, codecs
import io, os, re
import subprocess, shutil

default_encoding = 'cp1250' # PDF file meta data default encoding (maybe platform dependent)
sys.stdout = codecs.getwriter('utf8')(sys.stdout)
sys.stderr = codecs.getwriter('utf8')(sys.stderr)

output_directory = sys.argv[1]
if not os.path.exists(output_directory):
	os.mkdirs( output_directory )

# Rename science articles
def rename_articles():

	parsed = subprocess.Popen(["parse_articles.py"], shell=True, stdin=sys.stdin, stdout=subprocess.PIPE)
	parsed.stdout = codecs.getwriter('utf8')(parsed.stdout)
	
	# For each pdf file
	for line in parsed.stdout:
		
		line = line.strip()
		(pdffile, title, authors, date, abstract) = line.split("\t"); # name for validation
		
		# Rename in case all data is available
		if title and authors and date:
			title = title.replace(" ", "_").replace("-", "_")
			first_author = authors.split(",")[0].replace(" ", "_")
			filename = "_".join([first_author, title, date])
			filepath = output_directory + "/" + filename + ".pdf"
			shutil.copy(pdffile, filepath)
			print "%s\t%s" % (pdffile, filepath)
		

if __name__ == "__main__":
	rename_articles()