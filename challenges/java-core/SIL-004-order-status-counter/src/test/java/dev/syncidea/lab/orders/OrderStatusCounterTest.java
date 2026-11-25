package dev.syncidea.lab.orders;

import static dev.syncidea.lab.orders.OrderStatusCounter.Status.*;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

class OrderStatusCounterTest {
    @Test
    void countsEachOfTheEncounteredStatuses() {
        assertEquals(Map.of(NEW, 1, PAID, 2, CANCELLED, 3),
                OrderStatusCounter.countByStatus(List.of(PAID, NEW, CANCELLED, PAID, CANCELLED, CANCELLED)));
    }

    @Test
    void omitsStatusesThatAreNotPresent() {
        assertEquals(Map.of(CANCELLED, 2), OrderStatusCounter.countByStatus(List.of(CANCELLED, CANCELLED)));
    }

    @Test
    void returnsEmptyCountsForAnEmptyList() {
        assertEquals(Map.of(), OrderStatusCounter.countByStatus(List.of()));
    }

    @Test
    void leavesSourceListUntouched() {
        var input = new ArrayList<>(List.of(PAID, NEW, PAID));
        var before = List.copyOf(input);

        assertEquals(Map.of(PAID, 2, NEW, 1), OrderStatusCounter.countByStatus(input));
        assertEquals(before, input);
    }

    @Test
    void callsDoNotAccumulateCountsAcrossInputs() {
        OrderStatusCounter.countByStatus(List.of(NEW, NEW));
        assertEquals(Map.of(PAID, 1), OrderStatusCounter.countByStatus(List.of(PAID)));
    }

    @Test
    void rejectsNullListOrElement() {
        assertThrows(NullPointerException.class, () -> OrderStatusCounter.countByStatus(null));
        assertThrows(NullPointerException.class,
                () -> OrderStatusCounter.countByStatus(Arrays.asList(NEW, null)));
    }
}
