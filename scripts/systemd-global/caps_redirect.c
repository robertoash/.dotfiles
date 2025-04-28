// caps2hyper_doubletap.c
#include <stdio.h>
#include <linux/input-event-codes.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/time.h>
#include <stdbool.h>
#include <string.h>

#define DOUBLE_TAP_MS 300

struct input_event {
    struct timeval time;
    unsigned short type;
    unsigned short code;
    int value;
};

void emit(int fd, unsigned short type, unsigned short code, int value) {
    struct input_event ev = {0};
    gettimeofday(&ev.time, NULL);
    ev.type = type;
    ev.code = code;
    ev.value = value;
    write(fd, &ev, sizeof(ev));
}

long time_diff_ms(struct timeval a, struct timeval b) {
    return (b.tv_sec - a.tv_sec) * 1000 + (b.tv_usec - a.tv_usec) / 1000;
}

int main() {
    struct input_event ev;
    struct timeval last_caps_release = {0};
    bool caps_down = false;

    while (read(STDIN_FILENO, &ev, sizeof(ev)) > 0) {
        if (ev.type == EV_KEY && ev.code == KEY_CAPSLOCK) {
            if (ev.value == 1) {  // key down
                emit(STDOUT_FILENO, EV_KEY, KEY_LEFTCTRL, 1);
                emit(STDOUT_FILENO, EV_KEY, KEY_LEFTALT, 1);
                emit(STDOUT_FILENO, EV_KEY, KEY_LEFTMETA, 1);
                emit(STDOUT_FILENO, EV_KEY, KEY_LEFTSHIFT, 1);
                caps_down = true;
            } else if (ev.value == 0) {  // key up
                emit(STDOUT_FILENO, EV_KEY, KEY_LEFTCTRL, 0);
                emit(STDOUT_FILENO, EV_KEY, KEY_LEFTALT, 0);
                emit(STDOUT_FILENO, EV_KEY, KEY_LEFTMETA, 0);
                emit(STDOUT_FILENO, EV_KEY, KEY_LEFTSHIFT, 0);

                // Check for double tap
                struct timeval now;
                gettimeofday(&now, NULL);
                if (time_diff_ms(last_caps_release, now) < DOUBLE_TAP_MS) {
                    // Send real CapsLock
                    emit(STDOUT_FILENO, EV_KEY, KEY_CAPSLOCK, 1);
                    emit(STDOUT_FILENO, EV_KEY, KEY_CAPSLOCK, 0);
                    // Reset to avoid triple tap confusion
                    last_caps_release.tv_sec = 0;
                    last_caps_release.tv_usec = 0;
                } else {
                    last_caps_release = now;
                }

                caps_down = false;
            }
            continue;
        }

        write(STDOUT_FILENO, &ev, sizeof(ev));  // pass through everything else
    }

    return 0;
}
