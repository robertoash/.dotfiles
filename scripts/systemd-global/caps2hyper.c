// caps2hyper.c
#include <stdio.h>
#include <linux/input-event-codes.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/time.h>


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

int main() {
    struct input_event ev;
    while (read(STDIN_FILENO, &ev, sizeof(ev)) > 0) {
        if (ev.type == EV_KEY && ev.code == KEY_CAPSLOCK) {
            if (ev.value == 1) {  // key down
                emit(STDOUT_FILENO, EV_KEY, KEY_LEFTCTRL, 1);
                emit(STDOUT_FILENO, EV_KEY, KEY_LEFTALT, 1);
                emit(STDOUT_FILENO, EV_KEY, KEY_LEFTMETA, 1);
                emit(STDOUT_FILENO, EV_KEY, KEY_LEFTSHIFT, 1);
            } else if (ev.value == 0) {  // key up
                emit(STDOUT_FILENO, EV_KEY, KEY_LEFTCTRL, 0);
                emit(STDOUT_FILENO, EV_KEY, KEY_LEFTALT, 0);
                emit(STDOUT_FILENO, EV_KEY, KEY_LEFTMETA, 0);
                emit(STDOUT_FILENO, EV_KEY, KEY_LEFTSHIFT, 0);
            }
            // Don't emit the original CapsLock event
        } else {
            write(STDOUT_FILENO, &ev, sizeof(ev));  // pass through everything else
        }
    }
    return 0;
}
