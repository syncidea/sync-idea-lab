package dev.syncidea.lab.stock;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.api.Test;

class StockCounterTest {
    @Test
    void countsEveryQuantityAtOrBelowThreshold() {
        assertEquals(4, StockCounter.countLowStock(new int[]{7, 2, 0, 3, 2, 1}, 2));
    }

    @Test
    void countsOnlyZeroesWhenThresholdIsZero() {
        assertEquals(2, StockCounter.countLowStock(new int[]{0, 1, 0, Integer.MAX_VALUE}, 0));
    }

    @Test
    void handlesEmptyArrayAndNoMatches() {
        assertEquals(0, StockCounter.countLowStock(new int[]{}, 5));
        assertEquals(0, StockCounter.countLowStock(new int[]{6, 7}, 5));
    }

    @Test
    void acceptsMaximumThresholdAndPreservesInput() {
        int[] quantities = {Integer.MAX_VALUE, 1, 0, 15};
        int[] before = quantities.clone();

        assertEquals(4, StockCounter.countLowStock(quantities, Integer.MAX_VALUE));
        assertArrayEquals(before, quantities);
    }

    @Test
    void rejectsNullArray() {
        assertThrows(NullPointerException.class, () -> StockCounter.countLowStock(null, 2));
    }

    @Test
    void rejectsNegativeInputs() {
        assertThrows(IllegalArgumentException.class, () -> StockCounter.countLowStock(new int[]{}, -1));
        assertThrows(IllegalArgumentException.class, () -> StockCounter.countLowStock(new int[]{0, 5, -1}, 1));
    }
}
