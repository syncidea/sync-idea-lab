package dev.syncidea.lab.booking;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.LocalTime;
import org.junit.jupiter.api.Test;

class BookingWindowTest {
    private static final LocalTime OPEN = LocalTime.of(9, 0);
    private static final LocalTime CLOSE = LocalTime.of(17, 0);

    @Test
    void includesOpeningAndInterior() {
        assertTrue(BookingWindow.contains(OPEN, CLOSE, OPEN));
        assertTrue(BookingWindow.contains(OPEN, CLOSE, LocalTime.of(12, 30)));
    }

    @Test
    void excludesClosingAndOutsideTimes() {
        assertFalse(BookingWindow.contains(OPEN, CLOSE, OPEN.minusMinutes(1)));
        assertFalse(BookingWindow.contains(OPEN, CLOSE, CLOSE));
        assertFalse(BookingWindow.contains(OPEN, CLOSE, CLOSE.plusMinutes(1)));
    }

    @Test
    void checksBoundariesAtNanosecondPrecision() {
        assertFalse(BookingWindow.contains(OPEN, CLOSE, OPEN.minusNanos(1)));
        assertTrue(BookingWindow.contains(OPEN, CLOSE, CLOSE.minusNanos(1)));
    }

    @Test
    void equalEndpointsFormAnEmptyWindow() {
        assertFalse(BookingWindow.contains(OPEN, OPEN, OPEN));
        assertFalse(BookingWindow.contains(OPEN, OPEN, OPEN.plusNanos(1)));
    }

    @Test
    void rejectsReversedWindow() {
        assertThrows(IllegalArgumentException.class, () -> BookingWindow.contains(CLOSE, OPEN, OPEN));
    }

    @Test
    void rejectsNullArguments() {
        assertThrows(NullPointerException.class, () -> BookingWindow.contains(null, CLOSE, OPEN));
        assertThrows(NullPointerException.class, () -> BookingWindow.contains(OPEN, null, OPEN));
        assertThrows(NullPointerException.class, () -> BookingWindow.contains(OPEN, CLOSE, null));
    }
}
