function dracut-rebuild --description "Rebuild all dracut images using pkgbase naming (like EndeavourOS hooks)"
    # Check if we're root
    if test (id -u) -ne 0
        echo "🚫 This function must be run as root (use sudo)"
        return 1
    end

    # Source dracut config if it exists
    if test -f /etc/eos-dracut.conf
        source /etc/eos-dracut.conf
    end

    # Set quiet mode if configured
    set dracut_extra_params ""
    if test "$DRACUT_QUIET" = "true"
        set dracut_extra_params " --quiet"
    end

    echo "🔧 Rebuilding all dracut images using pkgbase naming..."

    # Loop through all kernel module directories
    for kernel_dir in /usr/lib/modules/*
        if not test -d "$kernel_dir"
            continue
        end
        
        # Check if pkgbase file exists
        if not test -f "$kernel_dir/pkgbase"
            echo "⚠️  Skipping "(basename "$kernel_dir")": missing pkgbase file"
            continue
        end
        
        # Check if this kernel belongs to a package (not orphaned)
        if not pacman -Qqo "$kernel_dir/pkgbase" >/dev/null 2>&1
            echo "⚠️  Skipping "(basename "$kernel_dir")": pkgbase not owned by any package"
            continue
        end
        
        # Read pkgbase and kernel version
        set pkgbase (cat "$kernel_dir/pkgbase")
        set kver (basename "$kernel_dir")
        
        echo "🚀 Building initramfs for $pkgbase ($kver)"
        
        # Build hostonly image
        dracut --force --hostonly --no-hostonly-cmdline$dracut_extra_params \
            "/boot/initramfs-$pkgbase.img" "$kver"
        
        # Build fallback image (if not disabled)
        if test "$NO_DRACUT_FALLBACK" != "true"
            echo "🚀 Building fallback initramfs for $pkgbase ($kver)"
            dracut --force --no-hostonly$dracut_extra_params \
                "/boot/initramfs-$pkgbase-fallback.img" "$kver"
        end
        
        # Copy vmlinuz to /boot with pkgbase naming
        if test -f "$kernel_dir/vmlinuz"
            echo "📦 Installing vmlinuz to /boot/vmlinuz-$pkgbase"
            install -Dm644 "$kernel_dir/vmlinuz" "/boot/vmlinuz-$pkgbase"
        end
    end

    echo "✅ Done! All initramfs images rebuilt with pkgbase naming."
    echo "📋 Generated files:"
    ls -la /boot/initramfs-*.img /boot/vmlinuz-* 2>/dev/null; or true
end
