package dev.syncidea.lab.orders;

import java.util.List;
import java.util.Map;

public final class OrderStatusCounter {
    private OrderStatusCounter() {
    }

    public enum Status {
        NEW, PAID, CANCELLED
    }

    public static Map<Status, Integer> countByStatus(List<Status> statuses) {
        throw new UnsupportedOperationException("Implement SIL-004");
    }
}
