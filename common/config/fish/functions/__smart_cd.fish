# Smart cd wrapper - passes through to z (zoxide)
function __smart_cd --wraps=z --description "cd wrapper for z"
    z $argv
end
