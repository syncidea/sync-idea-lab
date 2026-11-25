package dev.syncidea.lab.booking;

import java.time.LocalTime;

public final class BookingWindow {
    private BookingWindow() {
    }

    public static boolean contains(LocalTime opensAt, LocalTime closesAt, LocalTime time) {
        throw new UnsupportedOperationException("Implement SIL-005");
    }
}
