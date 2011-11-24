- generate MAMM.map with make-all run? [if, how?]
- might want to replace %.xml.ready by % [this would just act on the files w/o creating new]
- keep intermediary files: defined blank target .SECONDARY:
- .PHONY: ignore if/not target is up to date but always execute
- maybe $< for single execution

- --should cleanup on script and then annotate so plotting would catch errors--
-- actually, i already do (from cps, which should be fine)

- abs. paths in root makefile should be set with configure

- wajima still has the time in event issue (delete event to be able to plot)
- cvode has problems with jones 5pM



general:
- makefiles don't need to overwrite the all rule with ;, it should work as is
- vars should maybe have ?= for assgn so subdir makefiles can overwrite it before include
