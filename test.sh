#!/usr/bin/env sh

set -e

rm -rf -- output/
mkdir output/
mkdir output/00_lexer/
mkdir output/01_grouper/
mkdir output/10_parser/
mkdir output/11_namer/
mkdir output/12_flattener/
mkdir output/13_referencer/
mkdir output/20_normalizer/
mkdir output/30_compiler/
mkdir output/40_assembly/
mkdir output/50_executable/

if [ "$1" == "clear" ]; then
  exit 0
fi

if [ "$#" -ne 0 ]; then
  test_files="${@:1}"
else
  test_files=tests/*.znj
fi

for test in $test_files; do
  basename=$(basename $test)
  name="${basename%.*}"
  cat $test | ./00_lexer.py > output/00_lexer/$name.json
done

for test in $test_files; do
  basename=$(basename $test)
  name="${basename%.*}"
  cat output/00_lexer/$name.json | ./01_grouper.py > output/01_grouper/$name.json
done

for test in $test_files; do
  basename=$(basename $test)
  name="${basename%.*}"
  cat output/01_grouper/$name.json | ./10_parser.py > output/10_parser/$name.json
done

for test in $test_files; do
  basename=$(basename $test)
  name="${basename%.*}"
  cat output/10_parser/$name.json | ./11_namer.py > output/11_namer/$name.json
done

for test in $test_files; do
  basename=$(basename $test)
  name="${basename%.*}"
  cat output/11_namer/$name.json | ./12_flattener.py > output/12_flattener/$name.json
done

for test in $test_files; do
  basename=$(basename $test)
  name="${basename%.*}"
  cat output/12_flattener/$name.json | ./13_referencer.py > output/13_referencer/$name.json
done

for test in $test_files; do
  basename=$(basename $test)
  name="${basename%.*}"
  cat output/13_referencer/$name.json | ./20_normalizer.py > output/20_normalizer/$name.json
done

for test in $test_files; do
  basename=$(basename $test)
  name="${basename%.*}"
  cat output/20_normalizer/$name.json | ./30_compiler.py > output/30_compiler/$name.ll
done

for test in $test_files; do
  basename=$(basename $test)
  name="${basename%.*}"
  llc output/30_compiler/$name.ll -o output/40_assembly/$name.s
done

for test in $test_files; do
  basename=$(basename $test)
  name="${basename%.*}"
  clang -no-pie output/40_assembly/$name.s -o output/50_executable/$name
done
