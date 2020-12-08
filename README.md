# plagiarism-program-code

```
usage: main.py [-h] [-l L] [-p P] [-k] [-m] files files

A plagiarism detection tool for python code

positional arguments:
  files               the input files

optional arguments:
  -h, --help          show this help message and exit
  -l L                if AST line of the function >= value then output detail
                      (default: 4)
  -p P                if plagiarism percentage of the function >= value then
                      output detail (default: 0.5)
  -k, --keep-prints   keep print nodes
  -m, --module-level  process module level nodes
  ```
