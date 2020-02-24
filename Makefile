LIB = /usr/lib/python3/dist-packages

${LIB}/%.py: %.py
	sudo cp $< $@
	sudo chown root:root $@
	sudo chmod 0775 $@

install: ${LIB}/htmlbuilder.py ${LIB}/persist.py ${LIB}/coh_utils.py ${LIB}/geometry.py

${LIB}/htmlbuilder.py: htmlbuilder.py
${LIB}/persist.py: persist.py
${LIB}/coh_utils.py: coh_utils.py
${LIB}/geometry.py: geometry.py
