#!/usr/bin/env sh

set -e

rm -f -- output/0_lexer/*
rm -f -- output/1_parser/*
rm -f -- output/2_simplifier/*
rm -f -- output/3_normalizer/*
rm -f -- output/4_compiler/*
rm -f -- output/5_assembly/*
rm -f -- output/6_executable/*

if [ "$1" == "clear" ]; then
  exit 0
fi

test_files=tests/*.znj

for test in $test_files; do
  basename=$(basename $test)
  name="${basename%.*}"
  cat $test | ./0_lexer.py > output/0_lexer/$name.json
done

for test in $test_files; do
  basename=$(basename $test)
  name="${basename%.*}"
  cat output/0_lexer/$name.json | ./1_parser.py > output/1_parser/$name.json
done

for test in $test_files; do
  basename=$(basename $test)
  name="${basename%.*}"
  cat output/1_parser/$name.json | ./2_simplifier.py > output/2_simplifier/$name.json
done

for test in $test_files; do
  basename=$(basename $test)
  name="${basename%.*}"
  cat output/2_simplifier/$name.json | ./3_normalizer.py > output/3_normalizer/$name.json
done

for test in $test_files; do
  basename=$(basename $test)
  name="${basename%.*}"
  cat output/3_normalizer/$name.json | ./4_compiler.py > output/4_compiler/$name.ll
done

for test in $test_files; do
  basename=$(basename $test)
  name="${basename%.*}"
  llc output/4_compiler/$name.ll -o output/5_assembly/$name.s
done

for test in $test_files; do
  basename=$(basename $test)
  name="${basename%.*}"
  clang -no-pie output/5_assembly/$name.s -o output/6_executable/$name
done
