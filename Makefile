upload:
	rm -f dist/*
	python -m setuptools_scm
	python -m build
	echo
	echo "Upload version? or Ctrl+C"
	python -m setuptools_scm
	read confirm
	twine upload --repository optisolveapi  dist/optisolveapi-*.tar.gz