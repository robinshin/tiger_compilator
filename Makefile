# Automatisation de l'exécution de la commande tiger

TIGER_FILES = $(wildcard tests/*.tiger)
IR_FILES    = $(patsubst tests/%.tiger, /tmp/%.ir,$(TIGER_FILES))

all:irmake irtests


irmake: $(IR_FILES)
irtests: irmake

/tmp/%.ir : tests/%.tiger
	./tiger.py -ciId $< > $@

irtests: $(IR_FILES)
	irvm $<

.PHONY:clean
clean:
	rm /tmp/*.ir
