package dev.syncidea.lab.idempotency;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

@Timeout(value = 10, unit = TimeUnit.SECONDS, threadMode = Timeout.ThreadMode.SEPARATE_THREAD)
class IdempotencyRegistryTest {
    private static final Instant START = Instant.parse("2026-01-01T00:00:00Z");
    private MutableClock clock;
    private IdempotencyRegistry registry;

    @BeforeEach
    void setUp() {
        clock = new MutableClock(START);
        registry = new IdempotencyRegistry(Duration.ofSeconds(10), clock);
    }

    @Test
    void acceptsFirstAndRejectsDuplicate() {
        assertTrue(registry.tryAcquire("payment-42"));
        assertFalse(registry.tryAcquire("payment-42"));
    }

    @Test
    void rejectsOneNanosecondBeforeExpiry() {
        assertTrue(registry.tryAcquire("k"));
        clock.set(START.plusSeconds(10).minusNanos(1));
        assertFalse(registry.tryAcquire("k"));
    }

    @Test
    void acceptsExactlyAtExpiryAndStartsNewWindow() {
        assertTrue(registry.tryAcquire("k"));
        clock.set(START.plusSeconds(10));
        assertTrue(registry.tryAcquire("k"));
        assertFalse(registry.tryAcquire("k"));
        clock.set(START.plusSeconds(20));
        assertTrue(registry.tryAcquire("k"));
    }

    @Test
    void acceptsAfterExpiry() {
        assertTrue(registry.tryAcquire("k"));
        clock.set(START.plusSeconds(60));
        assertTrue(registry.tryAcquire("k"));
    }

    @Test
    void rejectedAttemptDoesNotExtendExpiry() {
        assertTrue(registry.tryAcquire("k"));
        clock.set(START.plusSeconds(9));
        assertFalse(registry.tryAcquire("k"));
        clock.set(START.plusSeconds(10));
        assertTrue(registry.tryAcquire("k"));
    }

    @Test
    void keysHaveIndependentWindows() {
        assertTrue(registry.tryAcquire("a"));
        clock.set(START.plusSeconds(5));
        assertTrue(registry.tryAcquire("b"));
        clock.set(START.plusSeconds(10));
        assertTrue(registry.tryAcquire("a"));
        assertFalse(registry.tryAcquire("b"));
    }

    @Test
    void preservesExactKeyIncludingCaseAndSpaces() {
        for (String key : List.of("Key", "key", " key", "key ", "ключ")) {
            assertTrue(registry.tryAcquire(key), key);
            assertFalse(registry.tryAcquire(new String(key)), key);
        }
    }

    @Test
    void instancesAreIndependent() {
        assertTrue(registry.tryAcquire("k"));
        assertTrue(new IdempotencyRegistry(Duration.ofSeconds(10), clock).tryAcquire("k"));
    }

    @Test
    void supportsNanosecondTtl() {
        var tiny = new IdempotencyRegistry(Duration.ofNanos(1), clock);
        assertTrue(tiny.tryAcquire("k"));
        assertFalse(tiny.tryAcquire("k"));
        clock.set(START.plusNanos(1));
        assertTrue(tiny.tryAcquire("k"));
    }

    @Test
    void nullArgumentsFailExplicitly() {
        assertThrows(NullPointerException.class, () -> new IdempotencyRegistry(null, clock));
        assertThrows(NullPointerException.class, () -> new IdempotencyRegistry(Duration.ofSeconds(1), null));
        assertThrows(NullPointerException.class, () -> registry.tryAcquire(null));
    }

    @ParameterizedTest
    @ValueSource(strings = {"", " ", "\t", "\n", " \t\n"})
    void rejectsBlankKeys(String key) {
        assertThrows(IllegalArgumentException.class, () -> registry.tryAcquire(key));
    }

    @Test
    void rejectsNonPositiveTtl() {
        assertThrows(IllegalArgumentException.class, () -> new IdempotencyRegistry(Duration.ZERO, clock));
        assertThrows(IllegalArgumentException.class, () -> new IdempotencyRegistry(Duration.ofNanos(-1), clock));
    }

    @Test
    void exactlyOneConcurrentWinnerInEachWindow() throws Exception {
        assertEquals(1, acquireTogether(48, false).stream().filter(Boolean::booleanValue).count());
        clock.set(START.plusSeconds(10));
        assertEquals(1, acquireTogether(48, false).stream().filter(Boolean::booleanValue).count());
    }

    @Test
    void concurrentDistinctKeysAllSucceed() throws Exception {
        assertTrue(acquireTogether(48, true).stream().allMatch(Boolean::booleanValue));
    }

    private List<Boolean> acquireTogether(int count, boolean distinctKeys) throws Exception {
        var ready = new CountDownLatch(count);
        var start = new CountDownLatch(1);
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            List<Future<Boolean>> futures = new ArrayList<>();
            for (int i = 0; i < count; i++) {
                String key = distinctKeys ? "key-" + i : "same-key";
                futures.add(executor.submit(() -> {
                    ready.countDown();
                    if (!start.await(3, TimeUnit.SECONDS)) {
                        throw new IllegalStateException("start barrier timed out");
                    }
                    return registry.tryAcquire(key);
                }));
            }
            assertTrue(ready.await(3, TimeUnit.SECONDS), "workers did not reach barrier");
            start.countDown();
            List<Boolean> results = new ArrayList<>();
            for (Future<Boolean> future : futures) {
                results.add(future.get(3, TimeUnit.SECONDS));
            }
            return results;
        } finally {
            start.countDown();
        }
    }

    private static final class MutableClock extends Clock {
        private final AtomicReference<Instant> now;

        private MutableClock(Instant initial) { now = new AtomicReference<>(initial); }
        void set(Instant instant) { now.set(instant); }
        @Override public ZoneId getZone() { return ZoneOffset.UTC; }
        @Override public Clock withZone(ZoneId zone) {
            return Clock.fixed(instant(), zone);
        }
        @Override public Instant instant() { return now.get(); }
    }
}
