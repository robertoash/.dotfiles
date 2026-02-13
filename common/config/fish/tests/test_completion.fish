#!/usr/bin/env fish
# Automated regression tests for the completion system
# Must be run in interactive mode: fish -i -C 'source common/config/fish/tests/test_completion.fish'

if not status is-interactive
    echo "ERROR: This test must run in interactive mode"
    echo "Usage: fish -i -C 'source /path/to/test_completion.fish'"
    exit 1
end

set -g pass 0
set -g fail 0

function assert_type -a expected description
    set -l actual (__completion_get_type)
    if test "$actual" = "$expected"
        set -g pass (math $pass + 1)
    else
        set -g fail (math $fail + 1)
        echo "FAIL: $description - expected '$expected', got '$actual'"
    end
end

# Source all completion functions if not already loaded
if not type -q __completion_get_type
    source (status dirname)/../functions/__completion_config.fish
end

# Test: directory commands
commandline -r "cd "; assert_type dirs "cd -> dirs"
commandline -r "z "; assert_type dirs "z -> dirs"
commandline -r "pushd "; assert_type dirs "pushd -> dirs"

# Test: file commands
commandline -r "nvim "; assert_type files "nvim -> files"
commandline -r "cat "; assert_type files "cat -> files"
commandline -r "bat "; assert_type files "bat -> files"

# Test: both commands
commandline -r "cp "; assert_type both "cp -> both"
commandline -r "mv "; assert_type both "mv -> both"

# Test: native commands
commandline -r "docker "; assert_type native "docker -> native"
commandline -r "git "; assert_type native "git -> native"

# Test: git subcommand detection
commandline -r "git add "; assert_type both "git add -> both"
commandline -r "git diff "; assert_type both "git diff -> both"

# Test: wrapper stripping
commandline -r "sudo nvim "; assert_type files "sudo nvim -> files"
commandline -r "sudo cd "; assert_type dirs "sudo cd -> dirs"

# Test: trigger words
commandline -r "ff"; assert_type "trigger:ff" "ff -> trigger:ff"
commandline -r "dd"; assert_type "trigger:dd" "dd -> trigger:dd"

# Test: empty command line
commandline -r ""; assert_type native "empty -> native"

# Test: unknown command defaults to both
commandline -r "someunknowncmd "; assert_type both "unknown -> both"

# Report
commandline -r ""
echo ""
echo "Results: $pass passed, $fail failed"
if test $fail -gt 0
    exit 1
end
