function no_paywall
    set -l paywall_url "https://www.removepaywall.com/search?url=$argv[1]"
    echo "Opening $paywall_url on qutebrowser"
    qute_profile rash "$paywall_url"
end