// caps2hyper_doubletap_fixed.c
#include <stdio.h>
#include <linux/input-event-codes.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/time.h>
#include <stdbool.h>
#include <string.h>
#include <poll.h>

#define HOLD_MS 300
#define CHECK_INTERVAL_MS 10
#define MAX_EVENTS 32

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

void emit_modifiers(int fd, int value) {
    emit(fd, EV_KEY, KEY_LEFTMETA, value);
    emit(fd, EV_KEY, KEY_LEFTCTRL, value);
    emit(fd, EV_KEY, KEY_LEFTALT, value);
    emit(fd, EV_KEY, KEY_LEFTSHIFT, value);
    emit(fd, EV_SYN, SYN_REPORT, 0);
}

int main() {
    struct input_event ev;
    struct timeval window_start = {0};
    bool window_active = false;
    bool caps_down = false;
    bool modifiers_active = false;
    bool decision_made = false;
    bool is_hyper_mode = false;
    int caps_press_count = 0;
    int caps_release_count = 0;

    struct input_event other_events[MAX_EVENTS];
    int other_event_count = 0;

    struct pollfd fds[1];
    fds[0].fd = STDIN_FILENO;
    fds[0].events = POLLIN;

    while (1) {
        // Check for window timeout
        if (window_active && !decision_made) {
            struct timeval now;
            gettimeofday(&now, NULL);
            if (time_diff_ms(window_start, now) >= HOLD_MS) {
                // Time to make a decision
                if (caps_press_count >= 2 && caps_release_count >= 1) {
                    // Double-tap: send CapsLock immediately
                    emit(STDOUT_FILENO, EV_KEY, KEY_CAPSLOCK, 1);
                    emit(STDOUT_FILENO, EV_KEY, KEY_CAPSLOCK, 0);
                    emit(STDOUT_FILENO, EV_SYN, SYN_REPORT, 0);
                    // Reset immediately
                    window_active = false;
                    decision_made = false;
                    caps_press_count = 0;
                    caps_release_count = 0;
                    other_event_count = 0;
                    continue;
                } else if (caps_press_count == 1 && caps_release_count == 1) {
                    // Single tap: send Escape and replay
                    emit(STDOUT_FILENO, EV_KEY, KEY_ESC, 1);
                    emit(STDOUT_FILENO, EV_KEY, KEY_ESC, 0);
                    emit(STDOUT_FILENO, EV_SYN, SYN_REPORT, 0);
                    for (int i = 0; i < other_event_count; i++) {
                        write(STDOUT_FILENO, &other_events[i], sizeof(struct input_event));
                    }
                    window_active = false;
                    decision_made = false;
                    caps_press_count = 0;
                    caps_release_count = 0;
                    other_event_count = 0;
                    continue;
                } else if (caps_press_count == 1 && caps_release_count == 0) {
                    // Held down: send modifiers down
                    emit_modifiers(STDOUT_FILENO, 1);
                    modifiers_active = true;
                    is_hyper_mode = true;
                    // Also, replay buffered keys with modifiers active
                    for (int i = 0; i < other_event_count; i++) {
                        write(STDOUT_FILENO, &other_events[i], sizeof(struct input_event));
                    }
                }
                decision_made = true;
            }
        }

        // Poll input
        int ret = poll(fds, 1, CHECK_INTERVAL_MS);
        if (ret <= 0) continue;

        if (read(STDIN_FILENO, &ev, sizeof(ev)) <= 0) break;

        if (ev.type == EV_KEY && ev.code == KEY_CAPSLOCK) {
            if (!window_active) {
                gettimeofday(&window_start, NULL);
                window_active = true;
            }

            if (ev.value == 1) {  // Press
                caps_down = true;
                caps_press_count++;
            } else if (ev.value == 0) {  // Release
                caps_down = false;
                caps_release_count++;
                if (modifiers_active) {
                    emit_modifiers(STDOUT_FILENO, 0);
                    modifiers_active = false;
                    is_hyper_mode = false;
                }
                // After key up, fully reset if decision was made
                if (decision_made) {
                    window_active = false;
                    decision_made = false;
                    caps_press_count = 0;
                    caps_release_count = 0;
                    other_event_count = 0;
                }
            }
            continue;
        } else if (window_active && !decision_made && other_event_count < MAX_EVENTS) {
            // Buffer events during window
            other_events[other_event_count++] = ev;
            continue;
        } else if (is_hyper_mode) {
            // If Hyper active, pass through events normally
            write(STDOUT_FILENO, &ev, sizeof(ev));
            continue;
        }

        // Pass through other events normally
        write(STDOUT_FILENO, &ev, sizeof(ev));
    }

    return 0;
}
