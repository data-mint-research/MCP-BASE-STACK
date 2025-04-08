#!/bin/bash
# This is a test script with shellcheck issues

# SC2034: foo appears unused. Verify use (or export if used externally).
foo=bar

# SC2086: Double quote to prevent globbing and word splitting.
echo $foo

# SC2154: var is referenced but not assigned.
echo $var

# SC2016: Expressions don't expand in single quotes, use double quotes for that.
echo 'The current directory is $PWD'

# SC2046: Quote this to prevent word splitting.
files=$(ls)

# SC2164: Use cd ... || exit in case cd fails.
cd /tmp

# SC2006: Use $(...) notation instead of legacy backticked `...`.
current_date=`date`

# Run a simple command
echo "Test completed"