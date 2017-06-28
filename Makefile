FILE_LIST = ./.installed_files.txt

.PHONY: pull push clean check install-only post-install uninstall

default: | pull clean check install

install: | install-only post-install

install-only:
	@ ./setup.py install --record $(FILE_LIST)

uninstall:
	@ while read FILE; do echo "Removing: $$FILE"; rm "$$FILE"; done < $(FILE_LIST)

clean:
	@ rm -Rf ./build

check:
	@ find . -type f -name "*.py" -not -path "./build/*" -exec pep8 --hang-closing {} \;

pull:
	@ git pull

push:
	@ git push

post-install:
	fixuwsgi appcmd-public appcmd-private
