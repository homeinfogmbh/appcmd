FILE_LIST = ./.installed_files.txt

.PHONY: pull push clean generate-bindings install uninstall

default: | pull clean generate-bindings install

generate-bindings:
	@ pyxbgen -u xsds/garbage_collection.xsd -m garbage_collection --module-prefix=appcmd.dom

install:
	@ ./setup.py install --record $(FILE_LIST)

uninstall:
	@ while read FILE; do echo "Removing: $$FILE"; rm "$$FILE"; done < $(FILE_LIST)

clean:
	@ rm -Rf ./build

pull:
	@ git pull

push:
	@ git push
