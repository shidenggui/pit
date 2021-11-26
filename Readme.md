# Pit

A pure Python implementation for Git based on `Buliding Git`

## Features

Supported commands:
* pit init
* pit add `<files>`
* pit commit -m `<message>`
* pit status
  * pit status --porcelain
* pit diff 
  * pit diff --cached
* pit branch -v
  * pit branch `<branch>` `<revision>`
  * pit branch -D `<branch>`
* pit checkout `<branch>/<revision>`
* pit log
  * pit log --oneline

