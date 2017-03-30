# Automatisation de l'exécution de la commande tiger

TIGER_FILES = $(wildcard tests/*.tiger)
IR_FILES    = $(patsubst tests/%.tiger, /tmp/%.ir,$(TIGER_FILES))

PRINTF  = /usr/bin/printf

.PHONY:irmake

all:irmake

irmake: $(IR_FILES)

/tmp/%.ir : tests/%.tiger
	@./tiger.py -ciId $^ > $@
	@$(PRINTF) "Running $@\nResult : "
	@irvm $@
	@$(PRINTF) "\nExpected : "
	@cat $^ | grep "//"
	@$(PRINTF) "\n"
	@rm $@
